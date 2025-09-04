"""Monitor third eye chakra metrics and flush inference queues."""

from __future__ import annotations

from pathlib import Path

from .base import heal

CHAKRA = "third_eye"
THRESHOLD = 0.93
SCRIPT_PATH = Path("scripts/chakra_healing/third_eye_inference_flush.py")


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


__all__ = ["heal_if_needed", "CHAKRA", "THRESHOLD", "SCRIPT_PATH"]
