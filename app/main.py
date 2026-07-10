"""FastAPI entrypoint (Fase 1: infra + healthcheck)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    configure_logging()
    settings = get_settings()
    logger.info("Iniciando %s", settings.app_name)
    init_db()  # cria tabelas SQLite se não existirem
    logger.info("Banco de dados inicializado")
    yield
    logger.info("%s encerrado", settings.app_name)


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}
