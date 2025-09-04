"""Monitor crown chakra metrics and perform full restarts."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "crown"
THRESHOLD = 0.95
SCRIPT_PATH = Path("scripts/chakra_healing/crown_full_restart.sh")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
