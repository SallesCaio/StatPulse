"""Teste end-to-end da Fase 3+5: Espanha x Belgica (fixtures, sem rede).

Simula a partida ao vivo, coleta eventos, classifica e entrega os destaques
via Notification Engine — provando o pipeline completo até a fase de testes.
"""
from __future__ import annotations

import asyncio
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import EventPriority, EventType, MatchStatus, Sport
from app.models.event import Event
from app.models.notification_log import NotificationLog
from app.models.preference import UserPreference
from app.models.user import User
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


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_message(self, chat_id: int, text: str, parse_mode: str | None = None) -> None:
        self.sent.append({"chat_id": chat_id, "text": text})


def _session_factory() -> sessionmaker:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, future=True)


def _build_provider() -> FakeProvider:
    match = ProviderMatch(
        external_id="999",
        sport=Sport.FOOTBALL,
        status=MatchStatus.LIVE,
        home_team_external_id="100",
        home_team_name="Espanha",
        away_team_external_id="200",
        away_team_name="Belgica",
        competition_external_id="1",
        competition_name="UEFA Nations League",
    )
    events = [
        ProviderEvent(external_id="ev1", match_external_id="999", type=EventType.GOAL, minute=23,
                      team_external_id="100", raw={"player": {"name": "Morata"}}),
        ProviderEvent(external_id="ev2", match_external_id="999", type=EventType.CARD, minute=45,
                      team_external_id="200", raw={"player": {"name": "De Bruyne"}}),
        ProviderEvent(external_id="ev3", match_external_id="999", type=EventType.SUBSTITUTION, minute=60,
                      team_external_id="100", raw={}),
        ProviderEvent(external_id="ev4", match_external_id="999", type=EventType.SHOT, minute=75,
                      team_external_id="200", raw={}),
        ProviderEvent(external_id="ev5", match_external_id="999", type=EventType.GOAL, minute=80,
                      team_external_id="100", raw={"player": {"name": "Torres"}}),
    ]
    return FakeProvider([match], {"999": events})


def _seed_user(factory: sessionmaker) -> None:
    with factory() as db:
        u = User(telegram_id=111)
        db.add(u)
        db.flush()
        db.add(UserPreference(user_id=u.id, sport=Sport.FOOTBALL, notify_p1=True, notify_p2=True, notify_p3=False))
        db.commit()


def test_e2e_spain_belgium() -> None:
    factory = _session_factory()
    _seed_user(factory)
    provider = _build_provider()
    bot = FakeBot()

    n1 = asyncio.run(collect_live_events(provider=provider, db_factory=factory, bot=bot))
    n2 = asyncio.run(collect_live_events(provider=provider, db_factory=factory, bot=bot))

    # 1) Coleta ingere 5 eventos e é idempotente
    assert n1 == 5
    assert n2 == 0

    # 2) Classificação correta (estilo OPTA)
    with factory() as db:
        rows = db.scalars(select(Event)).all()
        by_type = {e.type: e.priority for e in rows}
        assert by_type[EventType.GOAL] == EventPriority.P1
        assert by_type[EventType.CARD] == EventPriority.P1
        assert by_type[EventType.SUBSTITUTION] == EventPriority.P2
        assert by_type[EventType.SHOT] == EventPriority.P3

    # 3) Notificação: P1 (gol x2 + cartão = 3) + P2 (substituição = 1) = 4; P3 (chute) NÃO enviado
    assert len(bot.sent) == 4
    assert all("Chute" not in m["text"] for m in bot.sent)
    with factory() as db:
        logs = db.scalars(select(NotificationLog)).all()
        assert len(logs) == 4
        assert all(l.status == "sent" for l in logs)
