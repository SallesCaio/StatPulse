"""Camada de providers esportivos (Fase 3)."""
from __future__ import annotations

from app.core.config import get_settings
from app.providers.api_football import ApiFootballProvider
from app.providers.base import ProviderEvent, ProviderMatch, SportsProvider


def get_provider() -> SportsProvider | None:
    """Retorna o provider configurado ou None se faltar API key."""
    settings = get_settings()
    if not settings.api_football_key:
        return None
    return ApiFootballProvider(api_key=settings.api_football_key)
