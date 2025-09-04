"""Monitor sacral chakra metrics and reset GPU tasks."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "sacral"
THRESHOLD = 0.85
SCRIPT_PATH = Path("scripts/chakra_healing/sacral_gpu_recover.py")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
