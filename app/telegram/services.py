"""Lógica de cadastro e preferências (testável sem Telegram)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import EventPriority, Sport
from app.models.preference import UserPreference
from app.models.user import User


def register_user(
    db: Session, *, telegram_id: int, username: str | None, first_name: str | None
) -> User:
    """Cria ou atualiza o usuário a partir do Telegram."""
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        db.add(user)
        db.flush()
    else:
        user.username = username
        user.first_name = first_name
    return user


def ensure_preference(db: Session, user_id: int) -> UserPreference:
    """Garante que o usuário tenha um registro de preferências."""
    pref = db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if pref is None:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
        db.flush()
    return pref


def set_sport(db: Session, user_id: int, sport: Sport) -> UserPreference:
    pref = ensure_preference(db, user_id)
    pref.sport = sport
    return pref


def set_notify(
    db: Session, user_id: int, priority: EventPriority, enabled: bool
) -> UserPreference:
    pref = ensure_preference(db, user_id)
    setattr(pref, f"notify_{priority.value.lower()}", enabled)
    return pref


def set_language(db: Session, user_id: int, language: str) -> UserPreference:
    pref = ensure_preference(db, user_id)
    pref.language = language
    return pref


def get_preference(db: Session, user_id: int) -> UserPreference | None:
    return db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
