"""Enrich log records with emotional context.

This module defines a logging filter that is decoupled from any specific
emotion system. A callable returning ``(emotion, resonance)`` can be registered
via :func:`set_emotion_provider`; unset providers default to ``None`` values.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)


def _default_provider() -> Tuple[Optional[str], Optional[float]]:
    """Return default empty emotion and resonance values."""
    return None, None


_provider: Callable[[], Tuple[Optional[str], Optional[float]]] = _default_provider


def set_emotion_provider(
    provider: Callable[[], Tuple[Optional[str], Optional[float]]],
) -> None:
    """Register ``provider`` returning ``(emotion, resonance)``."""
    global _provider
    _provider = provider


class EmotionFilter(logging.Filter):
    """Append emotion and resonance fields to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        """Inject emotion and resonance into ``record``."""
        try:
            emotion, resonance = _provider()
        except RuntimeError as exc:  # pragma: no cover - safety
            logger.error("emotion provider runtime error: %s", exc, exc_info=exc)
            emotion, resonance = None, None
        except (TypeError, ValueError) as exc:  # pragma: no cover - safety
            logger.error(
                "emotion provider returned invalid data: %s", exc, exc_info=exc
            )
            emotion, resonance = None, None
        record.emotion = emotion
        record.resonance = resonance
        return True


__all__ = ["EmotionFilter", "set_emotion_provider"]
