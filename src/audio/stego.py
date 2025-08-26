from __future__ import annotations

"""Steganography helpers for ritual music."""

import json
from pathlib import Path
from functools import lru_cache

import numpy as np

from MUSIC_FOUNDATION.synthetic_stego_engine import encode_phrase

RITUAL_PROFILE = Path(__file__).resolve().parent / "ritual_profile.json"


@lru_cache(maxsize=None)
def load_ritual_profile(path: Path = RITUAL_PROFILE) -> dict:
    """Return ritual mappings loaded from ``path`` if available."""
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    return {}


def embed_phrase(wave: np.ndarray, ritual: str, emotion: str) -> np.ndarray:
    """Embed ritual phrase for ``emotion`` into ``wave`` if configured."""

    profile = load_ritual_profile()
    phrase = " ".join(profile.get(ritual, {}).get(emotion, []))
    if not phrase:
        return wave

    stego_wave = encode_phrase(phrase)
    if stego_wave.size < wave.size:
        stego_wave = np.pad(stego_wave, (0, wave.size - stego_wave.size))
    combined = wave[: stego_wave.size] + stego_wave[: wave.size]
    max_val = float(np.max(np.abs(combined)))
    if max_val > 0:
        combined /= max_val
    return combined.astype(np.float32)
