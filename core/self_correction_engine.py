from __future__ import annotations

"""Self-correct emotional output using recent feedback."""

import logging
from typing import Any, Dict

from INANNA_AI import voice_evolution
import emotional_state
import archetype_shift_engine

logger = logging.getLogger(__name__)


def _entry_for_emotion(emotion: str) -> Dict[str, Any]:
    """Return a minimal history entry for ``emotion``."""

    return {
        "emotion": emotion,
        "arousal": 0.5,
        "valence": 0.5,
        "sentiment": 0.0,
    }


def adjust(detected: str, intended: str, tolerance: float) -> None:
    """Adjust avatar tone when ``detected`` diverges from ``intended``."""

    logger.info(
        "Adjusting from %s to %s with tolerance %.3f", detected, intended, tolerance
    )

    current_layer = emotional_state.get_current_layer()
    expected = archetype_shift_engine.EMOTION_LAYER_MAP.get(detected.lower())
    if expected and current_layer and expected != current_layer:
        entry = _entry_for_emotion(detected)
        try:
            voice_evolution.update_voice_from_history([entry])
            logger.info(
                "Voice parameters tuned for %s due to archetype %s",
                detected,
                current_layer,
            )
        except Exception:
            logger.exception("voice evolution update failed")

    if detected == intended:
        logger.debug("No mismatch detected; skipping adjustment")
        return

    mismatch = 1.0
    if mismatch <= tolerance:
        logger.debug("Mismatch below tolerance (%.3f <= %.3f)", mismatch, tolerance)
        return

    entry = _entry_for_emotion(intended)
    try:
        voice_evolution.update_voice_from_history([entry])
        logger.info("Voice evolution updated for %s", intended)
    except Exception:
        logger.exception("voice evolution update failed")

    try:
        emotional_state.set_current_layer(intended)
    except Exception:
        logger.exception("failed setting emotion layer")


__all__ = ["adjust"]
