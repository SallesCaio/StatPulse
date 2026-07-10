"""Bot Telegram do StatPulse (Fase 2 + comandos de leitura Fase 2.5).

Telegram NUNCA acessa providers diretamente — só lê/escreve no banco
via `services` e recebe comandos do usuário.
"""
from __future__ import annotations

import asyncio
import logging

from telegram.ext import Application, CommandHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.telegram.handlers import help as help_module
from app.telegram.handlers import live as live_module
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
    app.add_handler(CommandHandler("ao_vivo", live_module.ao_vivo))
    app.add_handler(CommandHandler("ultimas", live_module.ultimas))
    return app


def main() -> None:
    from app.core.logging import configure_logging

    configure_logging()
    try:
        # ptb v22: run_polling() é síncrono e gerencia o event loop internamente.
        app = build_application()
        logger.info("Bot StatPulse iniciado (polling)")
        app.run_polling()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).error("Falha ao iniciar bot: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
