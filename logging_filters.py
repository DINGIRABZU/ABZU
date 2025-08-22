"""Logging filters that enrich records with emotional context.

Each filter attempts to query ``emotion_registry`` or a legacy
``emotional_state`` module, appending the emotion and resonance level to log
records.  Failures are logged but otherwise ignored.
"""

from __future__ import annotations

import logging

try:
    import emotion_registry
except ImportError:  # pragma: no cover - fallback
    emotion_registry = None  # type: ignore
    try:
        import emotional_state
    except ImportError:  # pragma: no cover - fallback
        emotional_state = None  # type: ignore


logger = logging.getLogger(__name__)


class EmotionFilter(logging.Filter):
    """Append emotion and resonance fields to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        emotion = None
        resonance = None
        if emotion_registry is not None:
            try:
                emotion = emotion_registry.get_last_emotion()
                resonance = emotion_registry.get_resonance_level()
            except (AttributeError, RuntimeError) as exc:
                logger.warning("emotion_registry fetch failed: %s", exc, exc_info=exc)
        elif emotional_state is not None:
            try:
                emotion = emotional_state.get_last_emotion()
                resonance = emotional_state.get_resonance_level()
            except (AttributeError, RuntimeError) as exc:
                logger.warning("emotional_state fetch failed: %s", exc, exc_info=exc)
        record.emotion = emotion
        record.resonance = resonance
        return True


__all__ = ["EmotionFilter"]
