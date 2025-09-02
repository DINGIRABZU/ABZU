"""Emotion to music parameter resolution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
from functools import lru_cache

from INANNA_AI import emotion_analysis, sonic_emotion_mapper
from MUSIC_FOUNDATION.inanna_music_COMPOSER_ai import (
    SCALE_MELODIES,
    load_emotion_music_map,
    select_music_params,
)

EMOTION_MAP = Path(__file__).resolve().parent / "emotion_music_map.yaml"


@lru_cache(maxsize=None)
def _load_map() -> dict:
    """Load and cache the emotion music mapping from YAML."""

    return load_emotion_music_map(EMOTION_MAP)


def resolve(
    emotion: str, archetype: str | None = None
) -> Tuple[float, List[str], str, str]:
    """Return tempo, melody, wave type and resolved archetype."""

    if archetype is None:
        try:  # pragma: no cover
            archetype = emotion_analysis.get_current_archetype()
        except Exception:  # pragma: no cover
            archetype = "Everyman"

    mapping = _load_map()
    params = sonic_emotion_mapper.map_emotion_to_sound(emotion, archetype)

    tempo, _scale, melody, _rhythm = select_music_params(
        emotion, mapping, params["tempo"]
    )

    if params.get("scale"):
        melody = SCALE_MELODIES.get(params["scale"], melody)

    wave_type = (
        "square"
        if any("guitar" in t or "trumpet" in t for t in params.get("timbre", []))
        else "sine"
    )

    return tempo, melody, wave_type, archetype
