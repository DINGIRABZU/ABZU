from __future__ import annotations

"""Utility script for mixing audio files.

``mix_audio`` analyzes each track to estimate tempo and key and chooses
transition parameters that can optionally be guided by an ``emotion``.
"""

import argparse
from pathlib import Path

import numpy as np
import yaml

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

from MUSIC_FOUNDATION.qnl_utils import quantum_embed
from . import audio_ingestion

EMOTION_MAP = Path(__file__).resolve().parent.parent / "emotion_music_map.yaml"


def _load(path: Path) -> tuple[np.ndarray, int]:
    if sf is None:
        raise RuntimeError("soundfile library not installed")
    data, sr = sf.read(path, always_2d=False)
    return np.asarray(data, dtype=float), sr


def _load_emotion_map() -> dict:
    try:
        with EMOTION_MAP.open("r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:  # pragma: no cover - configuration optional
        return {}


def mix_audio(
    paths: list[Path], emotion: str | None = None
) -> tuple[np.ndarray, int, dict[str, float | str | None]]:
    """Return mixed audio and transition info.

    Tempo and key are estimated for each track. When ``emotion`` is provided,
    tempo/key from :mod:`emotion_music_map` override the analyzed values.
    The returned ``info`` dictionary contains the chosen ``tempo`` and ``key``.
    """

    data, sr = _load(paths[0])
    mix = np.zeros_like(data, dtype=float)
    tempos: list[float] = []
    keys: list[str | None] = []
    for p in paths:
        d, s = _load(p)
        if s != sr:
            raise ValueError("sample rates differ")
        tempos.append(audio_ingestion.extract_tempo(d, s))
        keys.append(audio_ingestion.extract_key(d))
        if d.shape[0] > mix.shape[0]:
            mix = np.pad(mix, (0, d.shape[0] - mix.shape[0]))
        if d.shape[0] < mix.shape[0]:
            d = np.pad(d, (0, mix.shape[0] - d.shape[0]))
        mix += d
    mix /= len(paths)

    tempo = float(np.mean(tempos)) if tempos else 0.0
    key = keys[0] if keys else None

    if emotion:
        mapping = _load_emotion_map()
        emot_info = mapping.get(emotion, {})
        tempo = float(emot_info.get("tempo", tempo))
        key = emot_info.get("scale", key)

    return mix, sr, {"tempo": tempo, "key": key}


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--preview")
    parser.add_argument("--preview-duration", type=float, default=1.0)
    parser.add_argument("--qnl-text")
    parser.add_argument("--emotion")
    opts = parser.parse_args(args)

    if opts.qnl_text:
        quantum_embed(opts.qnl_text)

    mix, sr, info = mix_audio([Path(f) for f in opts.files], opts.emotion)
    if sf is None:
        raise RuntimeError("soundfile library not installed")
    sf.write(opts.output, mix, sr, subtype="PCM_16")
    if opts.preview:
        dur = int(sr * opts.preview_duration)
        sf.write(opts.preview, mix[:dur], sr, subtype="PCM_16")


if __name__ == "__main__":
    main()
