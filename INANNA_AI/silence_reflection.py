from __future__ import annotations

"""Detect sustained silence and suggest a short meaning."""

import numpy as np


def is_sustained_silence(
    wave: np.ndarray,
    sr: int,
    *,
    min_duration: float = 1.0,
    threshold: float = 1e-4,
) -> bool:
    """Return ``True`` if ``wave`` is mostly silent for ``min_duration`` seconds."""
    if len(wave) / sr < min_duration:
        return False
    return float(np.mean(np.abs(wave))) < threshold


def silence_meaning(
    wave: np.ndarray,
    sr: int,
    *,
    min_duration: float = 1.0,
    threshold: float = 1e-4,
) -> str:
    """Return a short text about the silence detected in ``wave``."""
    if is_sustained_silence(wave, sr, min_duration=min_duration, threshold=threshold):
        return "Extended silence – perhaps a pause for thought."
    return "Brief pause"


__all__ = ["is_sustained_silence", "silence_meaning"]
