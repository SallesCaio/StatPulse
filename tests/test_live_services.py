"""Testes dos comandos de leitura /ao_vivo e /ultimas (Fase 2.5)."""
from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import EventPriority, EventType, MatchStatus, Sport
from app.models.event import Event
from app.models.match import Match
from app.models.team import Team
from app.telegram.services_live import get_live_matches_summary, get_recent_matches


def _session_factory() -> sessionmaker:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, future=True)


def test_live_and_recent_services() -> None:
    factory = _session_factory()
    with factory() as db:
        spain = Team(external_id="100", name="Espanha", sport=Sport.FOOTBALL)
        belgium = Team(external_id="200", name="Belgica", sport=Sport.FOOTBALL)
        db.add_all([spain, belgium])
        db.flush()
        m = Match(
            external_id="999",
            sport=Sport.FOOTBALL,
            home_team_id=spain.id,
            away_team_id=belgium.id,
            status=MatchStatus.LIVE,
            score_home=1,
            score_away=0,
        )
        db.add(m)
        db.flush()
        db.add(Event(match_id=m.id, external_id="e1", type=EventType.GOAL, priority=EventPriority.P1, minute=23))
        db.add(Event(match_id=m.id, external_id="e2", type=EventType.CARD, priority=EventPriority.P1, minute=45))
        db.commit()

    with factory() as db:
        live = get_live_matches_summary(db)
        assert len(live) == 1
        assert live[0]["home"] == "Espanha"
        assert live[0]["score_home"] == 1
        assert live[0]["score_away"] == 0

        recent = get_recent_matches(db, limit=5)
        assert recent[0]["home"] == "Espanha"
        assert len(recent[0]["destaques"]) == 2  # gol + cartão são P1
