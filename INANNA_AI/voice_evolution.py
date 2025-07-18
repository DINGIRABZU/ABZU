"""Helpers to evolve INANNA's vocal style."""
from __future__ import annotations

from typing import Any, Dict, Iterable
from pathlib import Path
import os
import yaml

from . import emotional_synaptic_engine
import emotional_state

from . import db_storage
import vector_memory

import numpy as np

DEFAULT_VOICE_STYLES: Dict[str, Dict[str, float]] = {
    "neutral": {"speed": 1.0, "pitch": 0.0},
    "calm": {"speed": 0.9, "pitch": -1.0},
    "excited": {"speed": 1.1, "pitch": 1.0},
}

CONFIG_PATH = Path(__file__).resolve().parents[1] / "voice_config.yaml"
AVATAR_CONFIG_PATH = Path(__file__).resolve().parents[1] / "voice_avatar_config.yaml"
MUSIC_MAP_PATH = Path(__file__).resolve().parents[1] / "emotion_music_map.yaml"

SCALE_PITCH = {"C_major": 0.0, "A_minor": -3.0, "D_minor": 2.0}


def load_voice_config(path: Path = CONFIG_PATH) -> Dict[str, Dict[str, Any]]:
    """Return archetype settings loaded from ``path`` if it exists."""
    env_path = os.getenv("VOICE_AVATAR_CONFIG_PATH")
    if env_path:
        path = Path(env_path)
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        out: Dict[str, Dict[str, Any]] = {}
        for key, info in data.items():
            if isinstance(info, dict):
                out[key.lower()] = info
        return out
    return {}


def load_emotion_music_map(path: Path = MUSIC_MAP_PATH) -> Dict[str, Dict[str, Any]]:
    """Return emotion-to-music mapping loaded from ``path``."""
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {k.lower(): v for k, v in data.items() if isinstance(v, dict)}
    return {}


VOICE_CONFIG: Dict[str, Dict[str, Any]] = load_voice_config()
EMOTION_MUSIC_MAP: Dict[str, Dict[str, Any]] = load_emotion_music_map()

for info in VOICE_CONFIG.values():
    name = info.get("tone")
    if name:
        DEFAULT_VOICE_STYLES.setdefault(
            name.lower(),
            {
                "speed": float(info.get("speed", 1.0)),
                "pitch": float(info.get("pitch", 0.0)),
            },
        )


class VoiceEvolution:
    """Manage voice style parameters and allow future fine-tuning."""

    def __init__(self, styles: Dict[str, Dict[str, float]] | None = None) -> None:
        self.styles: Dict[str, Dict[str, float]] = (
            {k: v.copy() for k, v in (styles or DEFAULT_VOICE_STYLES).items()}
        )

    def base_params(self, emotion: str) -> Dict[str, float]:
        """Return stored parameters for ``emotion`` without filters."""
        return self.styles.get(emotion.lower(), self.styles["neutral"])

    def get_params(self, emotion: str) -> Dict[str, float]:
        """Return style parameters for ``emotion`` label including filters."""
        style = self.base_params(emotion)
        params = emotional_synaptic_engine.map_emotion_to_filters(
            emotion, style=style
        )
        return params

    def update_from_history(self, history: Iterable[Dict[str, Any]] | None = None) -> None:
        """Adjust voice styles based on recent emotion analyses.

        When ``history`` is ``None`` recent emotion logs are pulled from
        :mod:`vector_memory`. Updated profiles are automatically saved to the
        database via :func:`db_storage.save_voice_profiles`.
        """
        records = []
        try:
            records = vector_memory.query_vectors(filter={"type": "emotion"}, limit=20)
        except Exception:
            records = []
        if history is not None:
            records.extend(list(history))

        grouped: Dict[str, Dict[str, list[float]]] = {}
        for entry in records:
            emotion = entry.get("emotion")
            if emotion is None:
                continue
            if "arousal" not in entry or "valence" not in entry:
                continue
            data = grouped.setdefault(
                emotion, {"arousal": [], "valence": [], "sentiment": []}
            )
            data["arousal"].append(entry["arousal"])
            data["valence"].append(entry["valence"])
            if "sentiment" in entry and entry["sentiment"] is not None:
                data["sentiment"].append(entry["sentiment"])

        for emotion, values in grouped.items():
            arousal = float(np.mean(values["arousal"]))
            valence = float(np.mean(values["valence"]))
            sentiment = float(np.mean(values["sentiment"])) if values["sentiment"] else 0.0
            style = self.styles.setdefault(emotion, {"speed": 1.0, "pitch": 0.0})
            new_speed = round(1.0 + (arousal - 0.5) * 0.4, 3)
            new_pitch = round((valence - 0.5) * 2.0, 3)
            weight = 1.0 + sentiment
            style["speed"] = round((style["speed"] + new_speed * weight) / (1.0 + weight), 3)
            style["pitch"] = round((style["pitch"] + new_pitch * weight) / (1.0 + weight), 3)

        if grouped:
            try:
                db_storage.save_voice_profiles(self.styles)
            except Exception:
                pass

    def evolve_with_memory(self) -> None:
        """Update styles based on recent memory and log result."""
        try:
            history = vector_memory.query_vectors(filter={"type": "emotion"}, limit=20)
        except Exception:
            history = []
        if history:
            update_voice_from_history(history)
            emotion = history[-1].get("emotion") or emotional_state.get_last_emotion()
        else:
            emotion = emotional_state.get_last_emotion()

        filters = emotional_synaptic_engine.adjust_from_memory()
        if not filters:
            return

        emotion = emotion or "neutral"
        style = self.styles.setdefault(emotion, {"speed": 1.0, "pitch": 0.0})
        if "speed" in filters:
            style["speed"] = float(filters["speed"])
        if "pitch" in filters:
            style["pitch"] = float(filters["pitch"])

        try:
            vector_memory.add_vector(
                f"voice_profile_{emotion}",
                {
                    "emotion": emotion,
                    "speed": style.get("speed", 1.0),
                    "pitch": style.get("pitch", 0.0),
                    "model": os.getenv("CROWN_TTS_BACKEND", "gtts"),
                },
            )
        except Exception:
            pass

    def reset(self) -> None:
        """Reset styles to the default values."""
        self.styles = {k: v.copy() for k, v in DEFAULT_VOICE_STYLES.items()}

    def load_profiles(self, db_path: Path = db_storage.DB_PATH) -> None:
        """Populate styles from stored voice profiles."""
        self.styles.update(db_storage.fetch_voice_profiles(db_path=db_path))

    def store_profiles(self, db_path: Path = db_storage.DB_PATH) -> None:
        """Persist current styles to ``db_path``."""
        db_storage.save_voice_profiles(self.styles, db_path=db_path)


_evolver = VoiceEvolution()


def get_voice_params(emotion: str) -> Dict[str, float]:
    """Return stored parameters from the default :class:`VoiceEvolution`.

    The emotion-to-music map provides optional ``scale`` or ``pitch_shift``
    values. The resulting style includes a ``key`` field when a scale is
    defined and adjusts the pitch accordingly.
    """
    style = _evolver.base_params(emotion).copy()
    info = EMOTION_MUSIC_MAP.get(emotion.lower())
    if info:
        scale = info.get("scale")
        if scale:
            style["key"] = scale
            shift = SCALE_PITCH.get(scale)
            if shift is not None:
                style["pitch"] = style.get("pitch", 0.0) + float(shift)
        if "pitch_shift" in info:
            style["pitch"] = style.get("pitch", 0.0) + float(info["pitch_shift"])
    return style


def update_voice_from_history(history: Iterable[Dict[str, Any]] | None = None) -> None:
    """Update the default :class:`VoiceEvolution` with ``history`` or memory."""
    _evolver.update_from_history(history)


def load_profiles(db_path: Path = db_storage.DB_PATH) -> None:
    """Load voice profiles into the default :class:`VoiceEvolution`."""
    _evolver.load_profiles(db_path)


def store_profiles(db_path: Path = db_storage.DB_PATH) -> None:
    """Persist profiles from the default :class:`VoiceEvolution`."""
    _evolver.store_profiles(db_path)


__all__ = [
    "VoiceEvolution",
    "get_voice_params",
    "update_voice_from_history",
    "load_profiles",
    "store_profiles",
    "DEFAULT_VOICE_STYLES",
    "VOICE_CONFIG",
    "load_voice_config",
    "load_emotion_music_map",
]
