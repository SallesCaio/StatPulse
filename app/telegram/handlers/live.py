"""Handlers /ao_vivo e /ultimas (experiência sem partida ao vivo)."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import SessionLocal
from app.telegram.services_live import get_live_matches_summary, get_recent_matches


async def ao_vivo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    with SessionLocal() as db:
        live = get_live_matches_summary(db)
    if not live:
        await update.message.reply_text(
            "⚽ Nenhuma partida ao vivo no momento.\n"
            "Use /pref para configurar e /ultimas para ver o histórico.",
            parse_mode="Markdown",
        )
        return
    lines = ["*Partidas ao vivo*"]
    for m in live:
        lines.append(f"• {m['home']} {m['score_home']}x{m['score_away']} {m['away']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def ultimas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    with SessionLocal() as db:
        recent = get_recent_matches(db, limit=5)
    if not recent:
        await update.message.reply_text(
            "📭 Nenhuma partida no histórico ainda. O worker precisa coletar ao menos uma.",
            parse_mode="Markdown",
        )
        return
    lines = ["*Últimas partidas*"]
    for m in recent:
        dest = ", ".join(f"{d['minute']}'" for d in m["destaques"]) or "sem destaques"
        lines.append(f"• {m['home']} x {m['away']} ({m['status']}) — {dest}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
