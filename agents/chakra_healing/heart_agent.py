"""Monitor heart chakra metrics and repair memory."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "heart"
THRESHOLD = 0.88
SCRIPT_PATH = Path("scripts/chakra_healing/heart_memory_repair.py")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
