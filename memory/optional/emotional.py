"""No-op emotional layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, List, Sequence

EmotionFeatures = Sequence[float]


def log_emotion(features: EmotionFeatures, *args: Any, **kwargs: Any) -> None:
    """Discard emotion features."""


def fetch_emotion_history(*args: Any, **kwargs: Any) -> List[Any]:
    """Return an empty history."""
    return []


def get_connection(*args: Any, **kwargs: Any) -> None:
    """Return ``None`` to indicate no database connection."""
    return None


__all__ = ["log_emotion", "fetch_emotion_history", "get_connection", "EmotionFeatures"]
