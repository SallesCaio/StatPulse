"""Testes da Fase 5 (Notification Engine) com bot Telegram falso."""
from __future__ import annotations

import asyncio
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.engines.notification.dispatcher import dispatch_event
from app.models.enums import EventPriority, EventType, MatchStatus, Sport
from app.models.event import Event
from app.models.match import Match
from app.models.notification_log import NotificationLog
from app.models.preference import UserPreference
from app.models.team import Team
from app.models.user import User


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_message(self, chat_id: int, text: str, parse_mode: str | None = None) -> None:
        self.sent.append({"chat_id": chat_id, "text": text})


def _session_factory() -> sessionmaker:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, future=True, expire_on_commit=False)


def _seed_base(db) -> int:
    spain = Team(external_id="100", name="Espanha", sport=Sport.FOOTBALL)
    belgium = Team(external_id="200", name="Belgica", sport=Sport.FOOTBALL)
    db.add_all([spain, belgium])
    db.flush()
    match = Match(
        external_id="999",
        sport=Sport.FOOTBALL,
        home_team_id=spain.id,
        away_team_id=belgium.id,
        status=MatchStatus.LIVE,
    )
    db.add(match)
    db.flush()
    user = User(telegram_id=111, first_name="Caio")
    db.add(user)
    db.flush()
    db.add(
        UserPreference(
            user_id=user.id, sport=Sport.FOOTBALL, notify_p1=True, notify_p2=True, notify_p3=False
        )
    )
    db.commit()
    return match.id


def test_dispatch_p1_sends_to_football_user() -> None:
    factory = _session_factory()
    with factory() as db:
        match_id = _seed_base(db)
        ev = Event(
            match_id=match_id,
            external_id="e1",
            type=EventType.GOAL,
            priority=EventPriority.P1,
            minute=23,
            raw_payload={"player": {"name": "Morata"}},
        )
        db.add(ev)
        db.commit()
        ev_id = ev.id

    bot = FakeBot()
    n = asyncio.run(dispatch_event(ev_id, match_id, db_factory=factory, bot=bot))
    assert n == 1
    assert len(bot.sent) == 1
    assert "Gol" in bot.sent[0]["text"]
    assert "23'" in bot.sent[0]["text"]
    with factory() as db:
        logs = db.scalars(select(NotificationLog)).all()
        assert len(logs) == 1
        assert logs[0].status == "sent"


def test_dispatch_p3_not_sent_when_toggle_off() -> None:
    factory = _session_factory()
    with factory() as db:
        match_id = _seed_base(db)
        ev = Event(
            match_id=match_id,
            external_id="e2",
            type=EventType.SHOT,
            priority=EventPriority.P3,
            minute=75,
        )
        db.add(ev)
        db.commit()
        ev_id = ev.id

    bot = FakeBot()
    n = asyncio.run(dispatch_event(ev_id, match_id, db_factory=factory, bot=bot))
    assert n == 0
    assert bot.sent == []


def test_dispatch_ignores_basketball_user() -> None:
    factory = _session_factory()
    with factory() as db:
        match_id = _seed_base(db)
        buser = User(telegram_id=222)
        db.add(buser)
        db.flush()
        db.add(UserPreference(user_id=buser.id, sport=Sport.BASKETBALL, notify_p1=True))
        ev = Event(
            match_id=match_id,
            external_id="e3",
            type=EventType.GOAL,
            priority=EventPriority.P1,
            minute=10,
        )
        db.add(ev)
        db.commit()
        ev_id = ev.id

    bot = FakeBot()
    n = asyncio.run(dispatch_event(ev_id, match_id, db_factory=factory, bot=bot))
    assert n == 1  # só o usuário de futebol


def test_dispatch_no_token_no_bot_returns_zero() -> None:
    factory = _session_factory()
    with factory() as db:
        match_id = _seed_base(db)
        ev = Event(
            match_id=match_id,
            external_id="e4",
            type=EventType.GOAL,
            priority=EventPriority.P1,
            minute=5,
        )
        db.add(ev)
        db.commit()
        ev_id = ev.id

    n = asyncio.run(dispatch_event(ev_id, match_id, db_factory=factory))  # sem token, sem bot
    assert n == 0
