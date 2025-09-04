"""Self-correct emotional output using recent feedback."""

# @ip-sensitive: Emotion mismatch adjustment logic
from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np

import archetype_shift_engine
import emotional_state
from INANNA_AI import voice_evolution

logger = logging.getLogger(__name__)


def _entry_for_emotion(emotion: str) -> Dict[str, Any]:
    """Return a minimal history entry for ``emotion``."""

    return {
        "emotion": emotion,
        "arousal": 0.5,
        "valence": 0.5,
        "sentiment": 0.0,
    }


def adjust(
    detected: str,
    intended: str,
    tolerance: float,
    audio: np.ndarray | None = None,
) -> None:
    """Adjust avatar tone when ``detected`` diverges from ``intended``.

    When ``audio`` is provided the spectrum of the mismatched clip influences
    the arousal and valence passed to :mod:`voice_evolution`.
    """

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
    if audio is not None:
        try:
            spectrum = np.abs(np.fft.rfft(audio))
            if spectrum.size:
                energy = float(np.mean(spectrum))
                norm_energy = float(
                    np.clip(energy / (np.max(spectrum) + 1e-9), 0.0, 1.0)
                )
                freqs = np.arange(spectrum.size)
                centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum))
                norm_centroid = float(np.clip(centroid / spectrum.size, 0.0, 1.0))
                entry["arousal"] = norm_energy
                entry["valence"] = norm_centroid
        except Exception:
            logger.exception("spectral analysis failed")
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
