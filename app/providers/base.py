"""Contrato de provider esportivo (abstrato, agnóstico de API).

Define o schema canônico (normalizado) que qualquer API externa deve
entregar para o pipeline do StatPulse.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.enums import EventType, Sport


@dataclass
class ProviderMatch:
    external_id: str
    sport: Sport
    status: str  # live | scheduled | finished
    home_team_external_id: str | None
    home_team_name: str
    away_team_external_id: str | None
    away_team_name: str
    competition_external_id: str | None = None
    competition_name: str | None = None
    start_time: str | None = None


@dataclass
class ProviderEvent:
    external_id: str
    match_external_id: str
    type: EventType
    minute: int | None
    player_name: str | None = None
    secondary_player_name: str | None = None
    team_external_id: str | None = None
    raw: dict | None = None


class SportsProvider(ABC):
    @abstractmethod
    async def get_live_matches(self) -> list[ProviderMatch]:
        ...

    @abstractmethod
    async def get_match_events(self, match_external_id: str) -> list[ProviderEvent]:
        ...
