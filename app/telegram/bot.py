"""Bot Telegram do StatPulse (Fase 2).

Telegram NUNCA acessa providers diretamente — só lê/escreve no banco
via `services` e recebe comandos do usuário.
"""
from __future__ import annotations

import asyncio
import logging

from telegram.ext import Application, CommandHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.telegram import handlers as handlers_pkg
from app.telegram.handlers import help as help_module
from app.telegram.handlers import preferences as pref_module
from app.telegram.handlers import start as start_module

logger = get_logger(__name__)


def build_application() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado (veja .env.example)")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start_module.start))
    app.add_handler(CommandHandler("help", help_module.help_command))
    app.add_handler(CommandHandler("pref", pref_module.pref_command))
    return app


async def run_bot() -> None:
    app = build_application()
    logger.info("Bot StatPulse iniciado (polling)")
    await app.run_polling()


def main() -> None:
    from app.core.logging import configure_logging

    configure_logging()
    try:
        asyncio.run(run_bot())
    except RuntimeError as exc:
        logging.getLogger(__name__).error("Falha ao iniciar bot: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
