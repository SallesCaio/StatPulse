"""Enums do domínio StatPulse."""
from __future__ import annotations

import enum


class Sport(str, enum.Enum):
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    MMA = "mma"


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"


class EventType(str, enum.Enum):
    GOAL = "goal"
    ASSIST = "assist"
    CARD = "card"
    PENALTY = "penalty"
    SHOT = "shot"
    SHOT_ON_TARGET = "shot_on_target"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    SUBSTITUTION = "substitution"
    FOUL = "foul"
    CORNER = "corner"
    THROW_IN = "throw_in"
    GOAL_KICK = "goal_kick"
    POSSESSION = "possession"
    PASS = "pass"
    CROSS = "cross"


class EventPriority(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
