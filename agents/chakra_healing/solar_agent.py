"""Monitor solar chakra metrics and throttle CPU."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "solar"
THRESHOLD = 0.9
SCRIPT_PATH = Path("scripts/chakra_healing/solar_cpu_throttle.py")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
