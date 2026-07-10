"""Normalização de evento do provider para o modelo Event (Event Engine / F4)."""
from __future__ import annotations

from app.engines.event.classifier import classify
from app.providers.base import ProviderEvent


def normalize_event(ev: ProviderEvent) -> dict:
    """Converte ProviderEvent no dicionário de campos do modelo Event."""
    return {
        "type": ev.type,
        "priority": classify(ev.type),
        "minute": ev.minute,
        "team_external_id": ev.team_external_id,
        "raw": ev.raw,
    }
