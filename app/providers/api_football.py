"""Implementação do provider API-Football (RapidAPI)."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.logging import get_logger
from app.models.enums import EventType, Sport
from app.providers.base import ProviderEvent, ProviderMatch, SportsProvider

logger = get_logger(__name__)

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
HEADERS_HOST = "api-football-v1.p.rapidapi.com"


def _map_event_type(api_type: str, detail: str | None) -> EventType:
    """Mapeia o tipo/detail da API-Football para nosso EventType (estilo OPTA)."""
    t = (api_type or "").lower()
    d = (detail or "").lower()
    if t == "goal":
        return EventType.PENALTY if "penalty" in d else EventType.GOAL
    if t == "card":
        return EventType.CARD
    if t in ("subst", "substitution"):
        return EventType.SUBSTITUTION
    if t == "var":
        return EventType.PENALTY  # aproximação: VAR costuma envolver penalti/revogação
    return EventType.PASS  # fallback genérico


def _parse_matches(payload: dict[str, Any]) -> list[ProviderMatch]:
    out: list[ProviderMatch] = []
    for item in payload.get("response", []):
        fix = item.get("fixture", {})
        teams = item.get("teams", {})
        league = item.get("league", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        out.append(
            ProviderMatch(
                external_id=str(fix.get("id")),
                sport=Sport.FOOTBALL,
                status=(fix.get("status") or {}).get("short", "live"),
                home_team_external_id=str(home.get("id")) if home.get("id") else None,
                home_team_name=home.get("name", "?"),
                away_team_external_id=str(away.get("id")) if away.get("id") else None,
                away_team_name=away.get("name", "?"),
                competition_external_id=str(league.get("id")) if league.get("id") else None,
                competition_name=league.get("name"),
                start_time=fix.get("date"),
            )
        )
    return out


def _parse_events(payload: dict[str, Any]) -> list[ProviderEvent]:
    out: list[ProviderEvent] = []
    for item in payload.get("response", []):
        fixture = item.get("fixture", {})
        fix_id = str(fixture.get("id", ""))
        team = item.get("team", {})
        player = item.get("player", {})
        assist = item.get("assist", {})
        minute = item.get("time", {}).get("elapsed")
        detail = item.get("detail")
        out.append(
            ProviderEvent(
                external_id=f"{fix_id}-{minute}-{item.get('type')}-{player.get('name')}-{detail}",
                match_external_id=fix_id,
                type=_map_event_type(item.get("type", ""), detail),
                minute=int(minute) if minute is not None else None,
                player_name=player.get("name"),
                secondary_player_name=assist.get("name"),
                team_external_id=str(team.get("id")) if team.get("id") else None,
                raw=item,
            )
        )
    return out


class ApiFootballProvider(SportsProvider):
    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 10.0) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-RapidAPI-Key": self._api_key, "X-RapidAPI-Host": HEADERS_HOST}

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}{path}", headers=self._headers(), params=params or {}
            )
            if resp.status_code == 429:
                logger.warning("API-Football: rate limit (429). Reduzindo frequência.")
                return {"response": []}
            resp.raise_for_status()
            return resp.json()

    async def get_live_matches(self) -> list[ProviderMatch]:
        data = await self._get("/fixtures", params={"live": "all"})
        return _parse_matches(data)

    async def get_match_events(self, match_external_id: str) -> list[ProviderEvent]:
        data = await self._get("/fixtures/events", params={"fixture": match_external_id})
        return _parse_events(data)
