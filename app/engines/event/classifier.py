"""Classificação de eventos em prioridades (semente do Event Engine / F4).

P1 = instantâneos/destaques (gol, assistência, cartão, pênalti)
P2 = relevantes (finalizações no alvo, escanteio, substituição, falta)
P3 = contexto (chute, desarme, interceptação, etc.)
"""
from __future__ import annotations

from app.models.enums import EventPriority, EventType

_P1 = {EventType.GOAL, EventType.ASSIST, EventType.CARD, EventType.PENALTY}
_P2 = {EventType.SHOT_ON_TARGET, EventType.CORNER, EventType.SUBSTITUTION, EventType.FOUL}


def classify(event_type: EventType) -> EventPriority:
    if event_type in _P1:
        return EventPriority.P1
    if event_type in _P2:
        return EventPriority.P2
    return EventPriority.P3
