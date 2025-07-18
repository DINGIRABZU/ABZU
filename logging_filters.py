from __future__ import annotations

import logging

try:
    import emotion_registry
except Exception:  # pragma: no cover - fallback
    emotion_registry = None  # type: ignore
    try:
        import emotional_state
    except Exception:  # pragma: no cover - fallback
        emotional_state = None  # type: ignore

class EmotionFilter(logging.Filter):
    """Append emotion and resonance fields to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        emotion = None
        resonance = None
        if emotion_registry is not None:
            try:
                emotion = emotion_registry.get_last_emotion()
                resonance = emotion_registry.get_resonance_level()
            except Exception:
                pass
        elif emotional_state is not None:
            try:
                emotion = emotional_state.get_last_emotion()
                resonance = emotional_state.get_resonance_level()
            except Exception:
                pass
        record.emotion = emotion
        record.resonance = resonance
        return True

__all__ = ["EmotionFilter"]
