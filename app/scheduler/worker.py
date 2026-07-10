"""Worker de coleta (processo próprio, independente do Telegram).

Roda o APScheduler que dispara collect_live_events a cada POLL_INTERVAL_SECONDS.
Pode rodar sem TELEGRAM_BOT_TOKEN (coleta é independente do bot).
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.scheduler.jobs import collect_live_events

logger = get_logger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        collect_live_events,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="collect_live_events",
    )
    scheduler.start()
    logger.info("Worker de coleta iniciado (a cada %ds)", settings.poll_interval_seconds)
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown(wait=False)


def main() -> None:
    configure_logging()
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
