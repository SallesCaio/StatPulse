"""Job de coleta: provider -> normalização -> classificação -> persistência.

Executado pelo scheduler (APScheduler) a cada POLL_INTERVAL_SECONDS.
Persiste partidas, times, competição e eventos (idempotente via external_id).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.engines.event.classifier import classify
from app.models.competition import Competition
from app.models.enums import Sport
from app.models.event import Event
from app.models.match import Match
from app.models.team import Team
from app.providers import get_provider
from app.providers.base import SportsProvider

logger = get_logger(__name__)


def _upsert_team(db: Session, external_id: str | None, name: str) -> Team | None:
    if not external_id:
        return None
    team = db.scalar(select(Team).where(Team.external_id == external_id))
    if team is None:
        team = Team(external_id=external_id, name=name or "?", sport=Sport.FOOTBALL)
        db.add(team)
        db.flush()
    return team


def _upsert_match(db: Session, m: "ProviderMatchLike") -> Match:
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


async def collect_live_events(
    provider: SportsProvider | None = None,
    db_factory: sessionmaker = SessionLocal,
) -> int:
    """Coleta partidas ao vivo e ingere eventos normalizados+classificados.

    Retorna o número de eventos novos persistidos.
    """
    provider = provider or get_provider()
    if provider is None:
        logger.warning("Sem provider configurado (API_FOOTBALL_KEY). Pulando coleta.")
        return 0

    matches = await provider.get_live_matches()
    total = 0
    with db_factory() as db:
        for m in matches:
            match = _upsert_match(db, m)
            events = await provider.get_match_events(m.external_id)
            for ev in events:
                existing = db.scalar(select(Event).where(Event.external_id == ev.external_id))
                if existing is not None:
                    continue
                team = _upsert_team(db, ev.team_external_id, ev.player_name or "?") if ev.team_external_id else None
                db.add(
                    Event(
                        match_id=match.id,
                        external_id=ev.external_id,
                        type=ev.type,
                        priority=classify(ev.type),
                        minute=ev.minute,
                        team_id=team.id if team else None,
                        raw_payload=ev.raw,
                    )
                )
                total += 1
        db.commit()

    logger.info("Coleta concluída: %d novos eventos em %d partidas", total, len(matches))
    return total


# Tipo estrutural mínimo aceito por _upsert_match
class ProviderMatchLike:  # noqa: D101 (apenas anotação de contrato)
    external_id: str
    competition_external_id: str | None
    competition_name: str | None
    home_team_external_id: str | None
    home_team_name: str
    away_team_external_id: str | None
    away_team_name: str
    status: str
    start_time: str | None
