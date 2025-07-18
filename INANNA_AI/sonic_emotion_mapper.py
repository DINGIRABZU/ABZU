from __future__ import annotations

"""Map emotional context to audio synthesis parameters."""

from pathlib import Path
from typing import Any, Dict

import yaml


_PALETTE_PATH = Path(__file__).resolve().parents[1] / "emotional_tone_palette.yaml"
_MUSIC_MAP_PATH = Path(__file__).resolve().parents[1] / "emotion_music_map.yaml"
_QNL_MAP_PATH = Path(__file__).resolve().parents[1] / "qnl_to_music_layer_map.yaml"


def _load_mapping(path: Path) -> Dict[str, Dict[str, Any]]:
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return {str(k).lower(): v for k, v in data.items() if isinstance(v, dict)}
    return {}


EMOTIONAL_TONE_PALETTE: Dict[str, Dict[str, Any]] = _load_mapping(_PALETTE_PATH)
EMOTION_MUSIC_MAP: Dict[str, Dict[str, Any]] = _load_mapping(_MUSIC_MAP_PATH)
QNL_LAYER_MAP: Dict[str, Dict[str, Any]] = _load_mapping(_QNL_MAP_PATH)


def map_emotion_to_sound(emotion: str, archetype: str) -> Dict[str, Any]:
    """Return tempo, scale, timbre, harmonics and QNL params for ``emotion`` and ``archetype``."""
    ekey = str(emotion).lower()
    akey = str(archetype).lower()
    palette = EMOTIONAL_TONE_PALETTE.get(akey, {})
    emotion_ref = palette.get("emotion_ref", ekey)

    e_info = EMOTION_MUSIC_MAP.get(ekey, EMOTION_MUSIC_MAP.get("neutral", {}))
    tempo = float(e_info.get("tempo", 100.0))

    scale = palette.get("scale") or e_info.get("scale", "C_major")
    timbre = list(palette.get("instruments", []))
    harmonics = palette.get("harmonics")

    qnl_params = QNL_LAYER_MAP.get(emotion_ref.lower(), QNL_LAYER_MAP.get("neutral", {}))

    return {
        "tempo": tempo,
        "scale": scale,
        "timbre": timbre,
        "harmonics": harmonics,
        "qnl": qnl_params,
    }


__all__ = [
    "map_emotion_to_sound",
    "EMOTIONAL_TONE_PALETTE",
    "EMOTION_MUSIC_MAP",
    "QNL_LAYER_MAP",
]

