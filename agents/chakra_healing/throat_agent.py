"""Monitor throat chakra metrics and stabilize APIs."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "throat"
THRESHOLD = 0.92
SCRIPT_PATH = Path("scripts/chakra_healing/throat_api_stabilize.sh")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
