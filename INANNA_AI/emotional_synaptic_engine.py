from __future__ import annotations

"""Simple emotion-to-filter mapping with memory adjustment."""

from typing import Iterable, Dict, Any

from . import voice_evolution
import corpus_memory_logging

# Base filter parameters for supported emotions
_EMOTION_FILTERS: Dict[str, Dict[str, Any]] = {
    "neutral": {"speed": 1.0, "pitch": 0.0, "timbre": "neutral"},
    "joy": {"speed": 1.1, "pitch": 0.5, "timbre": "bright"},
    "calm": {"speed": 0.9, "pitch": -0.3, "timbre": "soft"},
    "fear": {"speed": 1.2, "pitch": 0.6, "timbre": "tense"},
}


def map_emotion_to_filters(
    emotion: str, memory: dict | None = None, *, style: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Return pitch, speed and timbre settings for ``emotion``.

    ``memory`` or ``style`` can override default parameters.
    """
    key = emotion.lower()
    params = _EMOTION_FILTERS.get(key, _EMOTION_FILTERS["neutral"]).copy()

    if style is None:
        style = voice_evolution.get_voice_params(key)
    params["speed"] = style.get("speed", params["speed"])
    params["pitch"] = style.get("pitch", params["pitch"])

    if memory:
        for name in ("speed", "pitch", "timbre"):
            if name in memory:
                params[name] = memory[name]
    return params


def adjust_from_memory(history: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Update voice profiles from ``history`` and return filters for the last emotion."""
    entries = list(history) if history is not None else corpus_memory_logging.load_interactions()
    if not entries:
        return {}

    voice_evolution.update_voice_from_history(entries)
    last_emotion = entries[-1].get("emotion", "neutral")
    return map_emotion_to_filters(last_emotion)


__all__ = ["map_emotion_to_filters", "adjust_from_memory"]
