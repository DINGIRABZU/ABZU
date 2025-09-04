"""Monitor root chakra metrics and trigger network restoration."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "root"
THRESHOLD = 0.8
SCRIPT_PATH = Path("scripts/chakra_healing/root_restore_network.sh")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
