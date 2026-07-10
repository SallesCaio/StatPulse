"""Testes da Fase 3: mapeamento API-Football, parsing e classificação."""
from __future__ import annotations

from app.engines.event.classifier import classify
from app.models.enums import EventPriority, EventType
from app.providers.api_football import _map_event_type, _parse_events, _parse_matches


def test_map_event_type() -> None:
    assert _map_event_type("Goal", "Normal Goal") == EventType.GOAL
    assert _map_event_type("Goal", "Penalty") == EventType.PENALTY
    assert _map_event_type("Card", "Yellow Card") == EventType.CARD
    assert _map_event_type("subst", None) == EventType.SUBSTITUTION
    assert _map_event_type("Var", "Penalty") == EventType.PENALTY


def test_parse_matches() -> None:
    payload = {
        "response": [
            {
                "fixture": {"id": 1, "date": "2026-01-01T00:00:00+00:00", "status": {"short": "LIVE"}},
                "teams": {"home": {"id": 10, "name": "A"}, "away": {"id": 20, "name": "B"}},
                "league": {"id": 99, "name": "Premier"},
            }
        ]
    }
    matches = _parse_matches(payload)
    assert len(matches) == 1
    m = matches[0]
    assert m.external_id == "1"
    assert m.home_team_name == "A"
    assert m.competition_external_id == "99"


def test_parse_events() -> None:
    payload = {
        "response": [
            {
                "fixture": {"id": 1},
                "time": {"elapsed": 45},
                "type": "Goal",
                "detail": "Normal Goal",
                "player": {"name": "X"},
                "assist": {"name": "Y"},
                "team": {"id": 10},
            },
            {
                "fixture": {"id": 1},
                "time": {"elapsed": 70},
                "type": "Card",
                "detail": "Yellow Card",
                "player": {"name": "Z"},
                "team": {"id": 20},
            },
        ]
    }
    events = _parse_events(payload)
    assert len(events) == 2
    assert events[0].type == EventType.GOAL
    assert events[0].minute == 45
    assert events[1].type == EventType.CARD


def test_classify() -> None:
    assert classify(EventType.GOAL) == EventPriority.P1
    assert classify(EventType.CARD) == EventPriority.P1
    assert classify(EventType.PENALTY) == EventPriority.P1
    assert classify(EventType.CORNER) == EventPriority.P2
    assert classify(EventType.SUBSTITUTION) == EventPriority.P2
    assert classify(EventType.PASS) == EventPriority.P3
    assert classify(EventType.SHOT) == EventPriority.P3
