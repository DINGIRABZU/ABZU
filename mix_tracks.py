from __future__ import annotations

"""Utility script for mixing audio files."""

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

from MUSIC_FOUNDATION.qnl_utils import quantum_embed


def _load(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(path, always_2d=False)
    return np.asarray(data, dtype=float), sr


def mix_audio(paths: list[Path]) -> tuple[np.ndarray, int]:
    data, sr = _load(paths[0])
    mix = np.zeros_like(data, dtype=float)
    for p in paths:
        d, s = _load(p)
        if s != sr:
            raise ValueError("sample rates differ")
        if d.shape[0] > mix.shape[0]:
            mix = np.pad(mix, (0, d.shape[0] - mix.shape[0]))
        if d.shape[0] < mix.shape[0]:
            d = np.pad(d, (0, mix.shape[0] - d.shape[0]))
        mix += d
    mix /= len(paths)
    return mix, sr


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--preview")
    parser.add_argument("--preview-duration", type=float, default=1.0)
    parser.add_argument("--qnl-text")
    opts = parser.parse_args(args)

    if opts.qnl_text:
        quantum_embed(opts.qnl_text)

    mix, sr = mix_audio([Path(f) for f in opts.files])
    sf.write(opts.output, mix, sr, subtype="PCM_16")
    if opts.preview:
        dur = int(sr * opts.preview_duration)
        sf.write(opts.preview, mix[:dur], sr, subtype="PCM_16")


if __name__ == "__main__":
    main()
