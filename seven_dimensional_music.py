"""Utility for simple seven-dimensional music features.

Provides helpers to convert embeddings to musical parameters and generate
audio used in tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

from typing import Any

from numpy.typing import NDArray

from MUSIC_FOUNDATION.qnl_utils import quantum_embed


def embedding_to_params(_emb: NDArray[np.floating]) -> tuple[float, float, float]:
    """Return pitch, tempo, and volume from an embedding.

    The mapping currently returns constant values and serves as a placeholder
    for more sophisticated audio parameter extraction.
    """
    return 0.0, 1.0, 1.0


def analyze_seven_planes(*_args: Any, **_kwargs: Any) -> dict:
    """Return dummy plane analysis."""
    return {
        "physical": {"element": "bass"},
        "emotional": {},
        "mental": {},
        "astral": {},
        "etheric": {},
        "celestial": {},
        "divine": {},
    }


def generate_quantum_music(
    context: str, emotion: str, *, output_dir: Path = Path(".")
) -> Path:
    """Generate a simple quantum-inspired tone.

    Saves a short sine wave as ``quantum.wav`` under ``output_dir`` and writes
    a companion JSON file with placeholder seven-plane analysis.
    """
    embed = quantum_embed(context)
    _pitch, _tempo, _vol = embedding_to_params(embed)
    sr = 44100
    duration = 0.25 + 0.05 * len(context)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * 220 * t)
    out = Path(output_dir) / "quantum.wav"
    if sf is None:
        raise RuntimeError("soundfile library not installed")
    sf.write(out, wave, sr, subtype="PCM_16")
    planes = analyze_seven_planes(wave, sr)
    planes.setdefault("physical", {})["element"] = "bass"
    (out.with_suffix(".json")).write_text(
        json.dumps({"planes": planes}), encoding="utf-8"
    )
    return out


def main(args: list[str] | None = None) -> None:
    """Run the command-line interface for quantum music generation.

    Parses arguments, copies audio, optionally embeds hidden data, and writes a
    JSON analysis file alongside the output.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--secret")
    opts = parser.parse_args(args)

    data, sr = sf.read(opts.input, always_2d=False)
    sf.write(opts.output, data, sr, subtype="PCM_16")

    if opts.secret:
        from MUSIC_FOUNDATION.synthetic_stego import embed_data

        embed_data(Path("human_layer.wav"), opts.secret)

    planes = analyze_seven_planes(data, sr)
    planes.setdefault("physical", {})["element"] = "bass"
    Path(opts.output).with_suffix(".json").write_text(
        json.dumps({"planes": planes}), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
