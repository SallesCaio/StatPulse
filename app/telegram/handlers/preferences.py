"""Handler /pref — gerencia preferências do usuário."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.enums import EventPriority, Sport
from app.telegram import services

logger = get_logger(__name__)

_VALID_SPORTS = {s.value: s for s in Sport}
_VALID_PRIORITIES = {p.value: p for p in EventPriority}


async def pref_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    user = update.effective_user
    args = context.args or []

    with SessionLocal() as db:
        db_user = services.register_user(
            db, telegram_id=user.id, username=user.username, first_name=user.first_name
        )
        pref = services.ensure_preference(db, db_user.id)

        if not args:
            await update.message.reply_text(_format_pref(pref), parse_mode="Markdown")
            return

        cmd, *rest = args
        cmd = cmd.lower()

        if cmd == "sport" and rest:
            sport = _VALID_SPORTS.get(rest[0].lower())
            if sport is None:
                await update.message.reply_text(
                    "Esporte inválido. Use: football, basketball ou mma."
                )
                return
            services.set_sport(db, db_user.id, sport)
            db.commit()
            await update.message.reply_text(
                f"Esporte definido: *{sport.value}*", parse_mode="Markdown"
            )
            return

        if cmd == "notify" and len(rest) >= 2:
            priority = _VALID_PRIORITIES.get(rest[0].upper())
            enabled = rest[1].lower() in ("on", "1", "sim", "true")
            if priority is None:
                await update.message.reply_text("Prioridade inválida. Use P1, P2 ou P3.")
                return
            services.set_notify(db, db_user.id, priority, enabled)
            db.commit()
            state = "ligado" if enabled else "desligado"
            await update.message.reply_text(
                f"{priority.value} {state}.", parse_mode="Markdown"
            )
            return

        if cmd == "lang" and rest:
            services.set_language(db, db_user.id, rest[0])
            db.commit()
            await update.message.reply_text(
                f"Idioma: *{rest[0]}*", parse_mode="Markdown"
            )
            return

        await update.message.reply_text(
            "Uso:\n"
            "/pref sport <football|basketball|mma>\n"
            "/pref notify <P1|P2|P3> <on|off>\n"
            "/pref lang <pt-BR|en>",
            parse_mode="Markdown",
        )


def _format_pref(pref) -> str:
    notify = []
    for p in EventPriority:
        on = getattr(pref, f"notify_{p.value.lower()}")
        notify.append(f"{p.value}:{'✅' if on else '❌'}")
    return (
        "*Suas preferências*\n"
        f"Esporte: *{pref.sport.value}*\n"
        f"Idioma: *{pref.language}*\n" + "\n".join(notify)
    )
