"""Testes offline do parser SportApi7 (sem rede) — trava o mapeamento de schema."""
from __future__ import annotations

from app.models.enums import EventPriority, EventType, MatchStatus
from app.providers.sportapi7 import _parse_incidents, _parse_matches


def test_parse_live_match() -> None:
    payload = {
        "events": [
            {
                "id": 12812994,
                "status": {"type": "inprogress", "code": 7, "description": "2nd half"},
                "homeTeam": {"id": 4698, "name": "Spain"},
                "awayTeam": {"id": 4717, "name": "Belgium"},
                "tournament": {"id": 3948, "name": "FIFA World Cup, Knockout"},
                "startTimestamp": 1783713600,
                "homeScore": {"current": 1},
                "awayScore": {"current": 1},
            }
        ]
    }
    matches = _parse_matches(payload)
    assert len(matches) == 1
    m = matches[0]
    assert m.external_id == "12812994"
    assert m.status == MatchStatus.LIVE
    assert m.home_team_name == "Spain"
    assert m.away_team_name == "Belgium"
    assert m.competition_name == "FIFA World Cup, Knockout"
    assert m.start_time is not None


def test_parse_incidents_maps_highlights_only() -> None:
    payload = {
        "home": {"id": 4698, "name": "Spain"},
        "away": {"id": 4717, "name": "Belgium"},
        "incidents": [
            {"incidentType": "goal", "time": 41, "isHome": True,
             "player": {"name": "Charles De Ketelaere"}, "id": 9001},
            {"incidentType": "card", "time": 43, "isHome": False,
             "player": {"name": "Pau Cubarsi"}, "id": 9002},
            {"incidentType": "substitution", "time": 55, "isHome": True,
             "playerIn": {"name": "A"}, "playerOut": {"name": "B"}, "id": 9003},
            {"incidentType": "period", "time": 45, "id": 9004},
            {"incidentType": "injuryTime", "time": 45, "id": 9005},
        ],
    }
    events = _parse_incidents(payload, "12812994", "4698", "4717")
    # period e injuryTime são ignorados -> só 3 destaques
    assert len(events) == 3
    by_type = {e.type: e for e in events}
    assert by_type[EventType.GOAL].minute == 41
    assert by_type[EventType.GOAL].team_external_id == "4698"  # isHome True -> home
    assert by_type[EventType.GOAL].player_name == "Charles De Ketelaere"
    assert by_type[EventType.CARD].team_external_id == "4717"  # isHome False -> away
    assert by_type[EventType.CARD].minute == 43
    assert by_type[EventType.SUBSTITUTION].minute == 55
