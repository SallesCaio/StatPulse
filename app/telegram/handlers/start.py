"""Handler /start — cadastro do usuário."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.telegram import services

logger = get_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or update.message is None:
        return

    with SessionLocal() as db:
        db_user = services.register_user(
            db, telegram_id=user.id, username=user.username, first_name=user.first_name
        )
        services.ensure_preference(db, db_user.id)
        db.commit()

    logger.info("Usuário %s registrado", user.id)
    await update.message.reply_text(
        f"Olá, {user.first_name or 'torcedor'}! 👋\n\n"
        "Eu sou o *StatPulse*, sua inteligência esportiva em tempo real.\n\n"
        "Use /pref para configurar o que quer acompanhar e /help para ver os comandos.",
        parse_mode="Markdown",
    )
