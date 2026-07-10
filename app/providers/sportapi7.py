"""Provider SportApi7 (RapidAPI) — futebol ao vivo (formato estilo Sofascore).

Endpoint de partidas ao vivo:
  GET /api/v1/sport/football/events/live
Endpoint de incidentes (gols/cartões/substituições) por partida:
  GET /api/v1/event/{id}/incidents

Observação de schema: no response de /incidents, os campos "home"/"away"
são cores de kit (não os ids). Os ids dos times vêm de /events/live
(homeTeam.id/awayTeam.id) e são cacheados aqui para resolver o time de cada
incidente via o flag "isHome".
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.logging import get_logger
from app.models.enums import EventType, MatchStatus, Sport
from app.providers.base import ProviderEvent, ProviderMatch, SportsProvider

logger = get_logger(__name__)

BASE_URL = "https://sportapi7.p.rapidapi.com"
HOST = "sportapi7.p.rapidapi.com"

_STATUS_MAP = {
    "inprogress": MatchStatus.LIVE,
    "finished": MatchStatus.FINISHED,
    "finishedafterprotest": MatchStatus.FINISHED,
    "notstarted": MatchStatus.SCHEDULED,
    "incoming": MatchStatus.SCHEDULED,
    "postponed": MatchStatus.SCHEDULED,
}

# Só os tipos que são destaques; "period"/"injuryTime" etc. são ignorados.
_INCIDENT_MAP = {
    "goal": EventType.GOAL,
    "card": EventType.CARD,
    "substitution": EventType.SUBSTITUTION,
    "var": EventType.PENALTY,
    "penalty": EventType.PENALTY,
}


def _normalize_status(status: dict | None) -> MatchStatus:
    if not status:
        return MatchStatus.SCHEDULED
    return _STATUS_MAP.get((status.get("type") or "").lower(), MatchStatus.SCHEDULED)


def _to_iso(ts: int | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _parse_matches(payload: dict[str, Any]) -> list[ProviderMatch]:
    out: list[ProviderMatch] = []
    for ev in payload.get("events", []):
        ht = ev.get("homeTeam", {}) or {}
        at = ev.get("awayTeam", {}) or {}
        tour = ev.get("tournament", {}) or {}
        out.append(
            ProviderMatch(
                external_id=str(ev.get("id")),
                sport=Sport.FOOTBALL,
                status=_normalize_status(ev.get("status")),
                home_team_external_id=str(ht.get("id")) if ht.get("id") else None,
                home_team_name=ht.get("name", "?"),
                away_team_external_id=str(at.get("id")) if at.get("id") else None,
                away_team_name=at.get("name", "?"),
                competition_external_id=str(tour.get("id")) if tour.get("id") else None,
                competition_name=tour.get("name"),
                start_time=_to_iso(ev.get("startTimestamp")),
            )
        )
    return out


def _parse_incidents(
    payload: dict[str, Any],
    match_external_id: str,
    home_id: str | None = None,
    away_id: str | None = None,
) -> list[ProviderEvent]:
    out: list[ProviderEvent] = []
    for inc in payload.get("incidents", []):
        itype = (inc.get("incidentType") or "").lower()
        etype = _INCIDENT_MAP.get(itype)
        if etype is None:
            continue  # period, injuryTime etc. não são destaques
        is_home = inc.get("isHome")
        team_id = home_id if is_home else away_id
        player = inc.get("player")
        player_name = player.get("name") if isinstance(player, dict) else None
        out.append(
            ProviderEvent(
                external_id=f"{match_external_id}-{inc.get('id')}-{itype}-{inc.get('time')}",
                match_external_id=match_external_id,
                type=etype,
                minute=inc.get("time"),
                player_name=player_name,
                team_external_id=team_id,
                raw=inc,
            )
        )
    return out


class SportApi7Provider(SportsProvider):
    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 20.0) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        # Cache: external_id da partida -> (home_external_id, away_external_id)
        self._match_teams: dict[str, tuple[str | None, str | None]] = {}

    def _headers(self) -> dict[str, str]:
        return {
            "X-RapidAPI-Key": self._api_key,
            "X-RapidAPI-Host": HOST,
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}{path}", headers=self._headers(), params=params or {}
            )
            if resp.status_code == 429:
                logger.warning("SportApi7: rate limit (429). Reduzindo frequência.")
                return {}
            resp.raise_for_status()
            return resp.json()

    async def _resolve_teams(
        self, match_external_id: str
    ) -> tuple[str | None, str | None]:
        if match_external_id in self._match_teams:
            return self._match_teams[match_external_id]
        data = await self._get(f"/api/v1/event/{match_external_id}")
        ht = (data.get("homeTeam") or {}).get("id")
        at = (data.get("awayTeam") or {}).get("id")
        pair = (str(ht) if ht else None, str(at) if at else None)
        self._match_teams[match_external_id] = pair
        return pair

    async def get_live_matches(self) -> list[ProviderMatch]:
        data = await self._get("/api/v1/sport/football/events/live")
        matches = _parse_matches(data)
        for m in matches:
            self._match_teams[m.external_id] = (m.home_team_external_id, m.away_team_external_id)
        return matches

    async def get_match_events(self, match_external_id: str) -> list[ProviderEvent]:
        data = await self._get(f"/api/v1/event/{match_external_id}/incidents")
        home_id, away_id = await self._resolve_teams(match_external_id)
        return _parse_incidents(data, match_external_id, home_id, away_id)
