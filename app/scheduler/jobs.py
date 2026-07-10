"""Job de coleta: provider -> normalização -> classificação -> persistência -> notificação."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.engines.event.normalizer import normalize_event
from app.engines.notification.dispatcher import dispatch_event
from app.models.competition import Competition
from app.models.enums import Sport
from app.models.event import Event
from app.models.match import Match
from app.models.team import Team
from app.providers import get_provider
from app.providers.base import ProviderMatch, SportsProvider

logger = get_logger(__name__)


def _upsert_team(db, external_id: str | None, name: str) -> Team | None:
    if not external_id:
        return None
    team = db.scalar(select(Team).where(Team.external_id == external_id))
    if team is None:
        team = Team(external_id=external_id, name=name or "?", sport=Sport.FOOTBALL)
        db.add(team)
        db.flush()
    return team


def _upsert_match(db, m: ProviderMatch) -> Match:
    match = db.scalar(select(Match).where(Match.external_id == m.external_id))
    if match is not None:
        return match
    competition = None
    if m.competition_external_id:
        competition = db.scalar(
            select(Competition).where(Competition.external_id == m.competition_external_id)
        )
        if competition is None:
            competition = Competition(
                external_id=m.competition_external_id,
                name=m.competition_name or "?",
                sport=Sport.FOOTBALL,
            )
            db.add(competition)
            db.flush()
    home = _upsert_team(db, m.home_team_external_id, m.home_team_name)
    away = _upsert_team(db, m.away_team_external_id, m.away_team_name)
    match = Match(
        external_id=m.external_id,
        sport=Sport.FOOTBALL,
        competition_id=competition.id if competition else None,
        home_team_id=home.id if home else None,
        away_team_id=away.id if away else None,
        status=m.status,
        start_time=m.start_time,
    )
    db.add(match)
    db.flush()
    return match


def _resolve_team_id(db, external_id: str | None) -> int | None:
    if not external_id:
        return None
    team = db.scalar(select(Team).where(Team.external_id == external_id))
    return team.id if team else None


async def collect_live_events(
    provider: SportsProvider | None = None,
    db_factory: sessionmaker = SessionLocal,
    bot=None,
) -> int:
    """Coleta partidas ao vivo, ingere eventos normalizados+classificados e notifica.

    Retorna o número de eventos novos persistidos.
    """
    provider = provider or get_provider()
    if provider is None:
        logger.warning("Sem provider configurado (API_FOOTBALL_KEY). Pulando coleta.")
        return 0

    matches = await provider.get_live_matches()
    new_event_ids: list[tuple[int, int]] = []
    total = 0
    with db_factory() as db:
        for m in matches:
            match = _upsert_match(db, m)
            events = await provider.get_match_events(m.external_id)
            for ev in events:
                existing = db.scalar(select(Event).where(Event.external_id == ev.external_id))
                if existing is not None:
                    continue
                norm = normalize_event(ev)
                team_id = _resolve_team_id(db, ev.team_external_id)
                event = Event(
                    match_id=match.id,
                    external_id=ev.external_id,
                    type=norm["type"],
                    priority=norm["priority"],
                    minute=norm["minute"],
                    team_id=team_id,
                    raw_payload=norm["raw"],
                )
                db.add(event)
                db.flush()
                new_event_ids.append((event.id, match.id))
                total += 1
        db.commit()

    logger.info("Coleta concluída: %d novos eventos em %d partidas", total, len(matches))

    # Notificação fora da transação de escrita (rede/Telegram).
    for event_id, match_id in new_event_ids:
        try:
            await dispatch_event(event_id, match_id, db_factory=db_factory, bot=bot)
        except Exception as exc:  # noqa: BLE001
            logger.error("Erro ao notificar evento %s: %s", event_id, exc)

    return total
