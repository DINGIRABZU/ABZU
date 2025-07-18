from __future__ import annotations
"""Analyze synthesized speech and update voice parameters."""

from typing import Dict, Any
import logging

from . import emotion_analysis, voice_evolution

logger = logging.getLogger(__name__)


def reflect(path: str) -> Dict[str, Any]:
    """Analyze ``path`` and update voice evolution history."""
    info = emotion_analysis.analyze_audio_emotion(path)
    try:
        voice_evolution.update_voice_from_history([info])
    except Exception:  # pragma: no cover - update may fail if optional deps missing
        logger.exception("voice evolution update failed")
    return info


__all__ = ["reflect"]
