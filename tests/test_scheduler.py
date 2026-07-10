"""Teste de integração da coleta (provider fake, sem rede)."""
from __future__ import annotations

import asyncio

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import EventPriority, EventType, MatchStatus, Sport
from app.models.event import Event
from app.models.match import Match
from app.providers.base import ProviderEvent, ProviderMatch, SportsProvider
from app.scheduler.jobs import collect_live_events


class FakeProvider(SportsProvider):
    def __init__(self, matches: list[ProviderMatch], events: dict[str, list[ProviderEvent]]) -> None:
        self._matches = matches
        self._events = events

    async def get_live_matches(self) -> list[ProviderMatch]:
        return self._matches

    async def get_match_events(self, match_external_id: str) -> list[ProviderEvent]:
        return self._events.get(match_external_id, [])


def _session_factory() -> sessionmaker:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, future=True)


def test_collect_ingests_and_is_idempotent() -> None:
    m = ProviderMatch(
        external_id="1",
        sport=Sport.FOOTBALL,
        status=MatchStatus.LIVE,
        home_team_external_id="10",
        home_team_name="A",
        away_team_external_id="20",
        away_team_name="B",
        competition_external_id="99",
        competition_name="Premier",
    )
    evs = [
        ProviderEvent(
            external_id="e1",
            match_external_id="1",
            type=EventType.GOAL,
            minute=45,
            player_name="X",
            team_external_id="10",
            raw={"x": 1},
        ),
        ProviderEvent(
            external_id="e2",
            match_external_id="1",
            type=EventType.CARD,
            minute=70,
            player_name="Z",
            team_external_id="20",
            raw={"y": 2},
        ),
    ]
    provider = FakeProvider([m], {"1": evs})
    db_factory = _session_factory()

    n1 = asyncio.run(collect_live_events(provider=provider, db_factory=db_factory))
    n2 = asyncio.run(collect_live_events(provider=provider, db_factory=db_factory))

    assert n1 == 2
    assert n2 == 0  # idempotente: não duplica

    with db_factory() as db:
        events = db.scalars(select(Event)).all()
        assert len(events) == 2
        goal = next(e for e in events if e.type == EventType.GOAL)
        assert goal.priority == EventPriority.P1
        assert goal.minute == 45
        match = db.scalar(select(Match).where(Match.external_id == "1"))
        assert match is not None
        assert match.home_team_id is not None
        assert match.competition_id is not None
