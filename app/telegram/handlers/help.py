"""Handler /help."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    text = (
        "*Comandos*\n"
        "/start — registrar e boas-vindas\n"
        "/pref — ver suas preferências\n"
        "/pref sport <football|basketball|mma> — esporte principal\n"
        "/pref notify <P1|P2|P3> <on|off> — liga/desliga notificações\n"
        "/pref lang <pt-BR|en> — idioma\n"
        "/help — esta ajuda"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
