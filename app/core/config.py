"""Configuração tipada da aplicação (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "StatPulse"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/statpulse.db"
    telegram_bot_token: str = ""
    api_football_key: str = ""
    provider: str = "api_football"  # api_football | sportapi7
    poll_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
