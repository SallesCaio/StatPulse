"""Consultas de leitura para os comandos /ao_vivo e /ultimas (Fase 2.5)."""
from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.competition import Competition
from app.models.enums import EventPriority, MatchStatus
from app.models.event import Event
from app.models.match import Match
from app.models.team import Team


def get_live_matches_summary(db=None) -> list[dict]:
    own = db is None
    db = db or SessionLocal()
    try:
        rows = (
            db.execute(select(Match).where(Match.status == MatchStatus.LIVE).order_by(Match.id.desc()))
            .scalars()
            .all()
        )
        out: list[dict] = []
        for m in rows:
            home = db.get(Team, m.home_team_id) if m.home_team_id else None
            away = db.get(Team, m.away_team_id) if m.away_team_id else None
            comp = db.get(Competition, m.competition_id) if m.competition_id else None
            out.append(
                {
                    "external_id": m.external_id,
                    "home": home.name if home else "?",
                    "away": away.name if away else "?",
                    "score_home": m.score_home,
                    "score_away": m.score_away,
                    "competition": comp.name if comp else None,
                }
            )
        return out
    finally:
        if own:
            db.close()


def get_recent_matches(db=None, limit: int = 5) -> list[dict]:
    own = db is None
    db = db or SessionLocal()
    try:
        rows = db.execute(select(Match).order_by(Match.id.desc()).limit(limit)).scalars().all()
        out: list[dict] = []
        for m in rows:
            home = db.get(Team, m.home_team_id) if m.home_team_id else None
            away = db.get(Team, m.away_team_id) if m.away_team_id else None
            events = (
                db.execute(select(Event).where(Event.match_id == m.id).order_by(Event.minute))
                .scalars()
                .all()
            )
            destaques = [
                {"minute": e.minute, "type": e.type.value}
                for e in events
                if e.priority == EventPriority.P1
            ]
            out.append(
                {
                    "home": home.name if home else "?",
                    "away": away.name if away else "?",
                    "status": m.status.value,
                    "destaques": destaques,
                }
            )
        return out
    finally:
        if own:
            db.close()
