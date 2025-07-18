from __future__ import annotations

"""Determine when to switch personality layers based on ritual cues or emotion."""

from typing import Iterable

import soul_state_manager

import emotion_registry

# Words or glyphs that signal a ritual transition
RITUAL_KEYWORDS: set[str] = {
    "ritual",
    "invoke",
    "summon",
    "☉",
    "☾",
    "❣",
    "⟁",
}

# Mapping from dominant emotions to personality layers when resonance is high
EMOTION_LAYER_MAP = {
    "anger": "nigredo_layer",
    "fear": "nigredo_layer",
    "sad": "nigredo_layer",
    "sadness": "nigredo_layer",
    "joy": "rubedo_layer",
    "love": "rubedo_layer",
    "excited": "rubedo_layer",
    "calm": "citrinitas_layer",
}


def _contains_keyword(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def maybe_shift_archetype(event: str, emotion: str) -> str | None:
    """Return a new layer if ``event`` or ``emotion`` triggers a shift."""
    if _contains_keyword(event, RITUAL_KEYWORDS):
        layer = "citrinitas_layer"
        try:
            soul_state_manager.update_archetype(layer)
        except Exception:
            pass
        return layer

    resonance = emotion_registry.get_resonance_level()
    current = emotion_registry.get_current_layer()
    if resonance >= 0.8:
        layer = EMOTION_LAYER_MAP.get(emotion.lower())
        if layer and layer != current:
            try:
                soul_state_manager.update_archetype(layer)
            except Exception:
                pass
            return layer
    return None


__all__ = ["maybe_shift_archetype"]
