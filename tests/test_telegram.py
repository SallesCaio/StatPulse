"""Testes da Fase 2: cadastro e preferências (lógica pura + registro de handlers)."""
from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import EventPriority, Sport
from app.models.preference import UserPreference
from app.models.user import User
from app.telegram import services


def _session_factory() -> sessionmaker:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, future=True)


def test_register_user_upsert() -> None:
    db = _session_factory()()
    u1 = services.register_user(db, telegram_id=10, username="a", first_name="A")
    db.commit()
    u2 = services.register_user(db, telegram_id=10, username="b", first_name="B")
    db.commit()
    assert u1.id == u2.id
    assert u2.username == "b"
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_ensure_preference_defaults() -> None:
    db = _session_factory()()
    u = services.register_user(db, telegram_id=20, username="x", first_name="X")
    db.commit()
    pref = services.ensure_preference(db, u.id)
    db.commit()
    assert pref.sport == Sport.FOOTBALL
    assert pref.notify_p1 is True and pref.notify_p2 is True and pref.notify_p3 is False
    assert pref.language == "pt-BR"
    # idempotente
    assert services.ensure_preference(db, u.id).id == pref.id


def test_set_sport_and_notify() -> None:
    db = _session_factory()()
    u = services.register_user(db, telegram_id=30, username="y", first_name="Y")
    db.commit()
    services.set_sport(db, u.id, Sport.BASKETBALL)
    services.set_notify(db, u.id, EventPriority.P1, False)
    services.set_language(db, u.id, "en")
    db.commit()
    pref = services.get_preference(db, u.id)
    assert pref is not None
    assert pref.sport == Sport.BASKETBALL
    assert pref.notify_p1 is False
    assert pref.notify_p2 is True
    assert pref.language == "en"


def test_application_registers_handlers(monkeypatch) -> None:
    import app.telegram.bot as bot
    from app.core.config import get_settings

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:fake")
    get_settings.cache_clear()

    app = bot.build_application()
    commands: set[str] = set()
    for h in app.handlers[0]:
        cmds = getattr(h, "commands", None)
        if cmds:
            commands.update(cmds)
    assert "start" in commands
    assert "pref" in commands
    assert "help" in commands
