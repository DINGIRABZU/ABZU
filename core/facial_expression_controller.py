from __future__ import annotations

"""Basic facial expression control utilities."""

from typing import Dict, Tuple

import numpy as np

import emotional_state

# Map emotions to simple RGB colours representing expressions.
# In a real renderer these would correspond to blendshape weights
# or bone pose targets.
EMOTION_MAP: Dict[str, Tuple[int, int, int]] = {
    "joy": (255, 215, 0),  # golden glow
    "anger": (255, 0, 0),  # red tint
    "sadness": (0, 0, 255),  # blue tint
    "neutral": (128, 128, 128),
}

def get_current_expression() -> Tuple[int, int, int]:
    """Return the expression colour for the last recorded emotion."""
    emotion = emotional_state.get_last_emotion() or "neutral"
    return EMOTION_MAP.get(emotion, EMOTION_MAP["neutral"])

def apply_expression(frame: np.ndarray, emotion: str | None) -> np.ndarray:
    """Return ``frame`` modified according to ``emotion``."""
    colour = EMOTION_MAP.get(emotion or "neutral", EMOTION_MAP["neutral"])
    modified = frame.copy()
    modified[:8, :8] = np.array(colour, dtype=np.uint8)
    return modified

__all__ = ["get_current_expression", "apply_expression"]
