"""Logging filters that enrich records with emotional context.

The filter is intentionally decoupled from any particular emotion module.  A
callable returning ``(emotion, resonance)`` can be registered via
``set_emotion_provider``.  If no provider is set the added fields default to
``None``.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional, Tuple


logger = logging.getLogger(__name__)

_provider: Callable[[], Tuple[Optional[str], Optional[float]]] = (
    lambda: (None, None)
)


def set_emotion_provider(
    provider: Callable[[], Tuple[Optional[str], Optional[float]]]
) -> None:
    """Register ``provider`` returning ``(emotion, resonance)``."""

    global _provider
    _provider = provider


class EmotionFilter(logging.Filter):
    """Append emotion and resonance fields to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        try:
            emotion, resonance = _provider()
        except Exception as exc:  # pragma: no cover - safety
            logger.warning("emotion provider failed: %s", exc, exc_info=exc)
            emotion, resonance = None, None
        record.emotion = emotion
        record.resonance = resonance
        return True


__all__ = ["EmotionFilter", "set_emotion_provider"]
