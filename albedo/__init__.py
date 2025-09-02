"""Core types for albedo state machine."""

from __future__ import annotations

from enum import Enum, IntEnum


class State(Enum):
    """Alchemical phases for the albedo machine."""

    ALBEDO = "albedo"
    CITRINITAS = "citrinitas"
    RUBEDO = "rubedo"
    NIGREDO = "nigredo"


class Magnitude(IntEnum):
    """Discrete trust magnitudes from 0 to 10."""

    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10


__all__ = ["State", "Magnitude"]
