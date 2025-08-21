from __future__ import annotations

"""High-level music analysis pipeline combining feature and emotion extraction."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

from audio.audio_ingestion import (extract_key, extract_mfcc, extract_tempo,
                                   load_audio)
from INANNA_AI.emotion_analysis import analyze_audio_emotion


@dataclass
class MusicAnalysisResult:
    """Container for the results of music analysis."""

    features: Dict[str, Any]
    emotion: Dict[str, Any]
    metadata: Dict[str, Any]


def extract_high_level_features(samples: "np.ndarray", sr: int) -> Dict[str, Any]:
    """Return a dictionary of high-level audio features."""

    if np is None:
        raise RuntimeError("numpy library not installed")
    mfcc = extract_mfcc(samples, sr).mean(axis=1).tolist()
    key = extract_key(samples)
    tempo = extract_tempo(samples, sr)
    return {"mfcc": mfcc, "key": key, "tempo": tempo}


def analyze_music(path: Path) -> MusicAnalysisResult:
    """Run the full music analysis pipeline for ``path``."""

    samples, sr = load_audio(path)
    features = extract_high_level_features(samples, sr)
    emotion = analyze_audio_emotion(str(path))
    metadata = {"path": str(path), "sr": sr, "duration": len(samples) / sr}
    return MusicAnalysisResult(features=features, emotion=emotion, metadata=metadata)


def main(argv: List[str] | None = None) -> None:
    """Command line interface for the music analysis pipeline."""

    import argparse

    parser = argparse.ArgumentParser(description="Analyze an audio file")
    parser.add_argument("file", type=Path, help="Path to an audio file")
    args = parser.parse_args(argv)

    result = analyze_music(args.file)
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
