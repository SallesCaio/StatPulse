"""Notification Engine (Fase 5): entrega de eventos aos usuários via Telegram."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from telegram import Bot

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.enums import EventPriority, EventType, Sport
from app.models.event import Event
from app.models.match import Match
from app.models.notification_log import NotificationLog
from app.models.preference import UserPreference
from app.models.team import Team
from app.models.user import User

logger = get_logger(__name__)

_EVENT_LABELS_PT: dict[EventType, str] = {
    EventType.GOAL: "Gol",
    EventType.ASSIST: "Assistência",
    EventType.CARD: "Cartão",
    EventType.PENALTY: "Pênalti",
    EventType.SUBSTITUTION: "Substituição",
    EventType.CORNER: "Escanteio",
    EventType.FOUL: "Falta",
    EventType.SHOT_ON_TARGET: "Finalização",
    EventType.SHOT: "Chute",
    EventType.TACKLE: "Desarme",
    EventType.INTERCEPTION: "Interceptação",
    EventType.THROW_IN: "Tiro de meta",
    EventType.CROSS: "Cruzamento",
    EventType.PASS: "Passe",
}


def _format_event_message(event: Event, home: str, away: str, team: str | None) -> str:
    minute = f"{event.minute}'" if event.minute is not None else ""
    label = _EVENT_LABELS_PT.get(event.type, event.type.value)
    player = ""
    if event.raw_payload:
        player = event.raw_payload.get("player", {}).get("name") or ""
    lines = [f"🔴 {minute} {label}"]
    if player:
        lines.append(f"👤 {player}")
    if team:
        lines.append(f"🏟️ {team}")
    lines.append(f"📊 {home} x {away}")
    return "\n".join(lines)


async def dispatch_event(
    event_id: int,
    match_id: int,
    db_factory: sessionmaker = SessionLocal,
    bot: Bot | None = None,
) -> int:
    """Envia o evento aos usuários aptos (futebol + toggle da prioridade).

    Retorna o número de mensagens enviadas. Sem token e sem bot => 0 (loga).
    """
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token and bot is None:
        logger.warning("Sem TELEGRAM_BOT_TOKEN; pulando notificação.")
        return 0
    bot = bot or Bot(token)

    with db_factory() as db:
        event = db.get(Event, event_id)
        match = db.get(Match, match_id)
        if event is None or match is None:
            return 0
        home = db.get(Team, match.home_team_id) if match.home_team_id else None
        away = db.get(Team, match.away_team_id) if match.away_team_id else None
        team = db.get(Team, event.team_id) if event.team_id else None

        col = f"notify_{event.priority.value.lower()}"
        users = (
            db.execute(
                select(User)
                .join(UserPreference)
                .where(UserPreference.sport == Sport.FOOTBALL)
                .where(getattr(UserPreference, col).is_(True))
            )
            .scalars()
            .all()
        )
        if not users:
            return 0

        text = _format_event_message(
            event,
            home.name if home else "?",
            away.name if away else "?",
            team.name if team else None,
        )
        sent = 0
        for u in users:
            try:
                await bot.send_message(chat_id=u.telegram_id, text=text, parse_mode="Markdown")
                db.add(NotificationLog(user_id=u.id, event_id=event.id, status="sent"))
                sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Falha ao notificar user %s: %s", u.id, exc)
                db.add(NotificationLog(user_id=u.id, event_id=event.id, status="failed"))
        db.commit()
        return sent
