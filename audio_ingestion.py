from __future__ import annotations

"""Audio ingestion helpers using librosa with optional Essentia and CLAP."""

from pathlib import Path
from typing import Tuple

import numpy as np
import librosa

try:  # pragma: no cover - optional dependency
    import essentia.standard as ess
except Exception:  # pragma: no cover - optional dependency
    ess = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from transformers import ClapProcessor, ClapModel
    import torch
except Exception:  # pragma: no cover - optional dependency
    ClapProcessor = None  # type: ignore
    ClapModel = None  # type: ignore
    torch = None  # type: ignore


def load_audio(path: Path, sr: int = 44100) -> Tuple[np.ndarray, int]:
    """Load audio using :func:`librosa.load`."""
    return librosa.load(path, sr=sr, mono=True)


def extract_mfcc(samples: np.ndarray, sr: int) -> np.ndarray:
    """Return MFCC features for ``samples``."""
    return librosa.feature.mfcc(y=samples, sr=sr)


def extract_key(samples: np.ndarray) -> str | None:
    """Return detected musical key using Essentia if available."""
    if ess is None:
        return None
    key, scale, _ = ess.KeyExtractor()(samples)
    return f"{key}:{scale}"


def extract_tempo(samples: np.ndarray, sr: int) -> float:
    """Return tempo estimated by Essentia when present or Librosa fallback."""
    if ess is None:
        tempo = librosa.beat.tempo(y=samples, sr=sr)
        return float(np.atleast_1d(tempo)[0])
    tempo, _ = ess.RhythmExtractor2013(method="multifeature")(samples)
    return float(tempo)


def embed_clap(samples: np.ndarray, sr: int) -> np.ndarray:
    """Return CLAP embedding of ``samples`` if the model is installed."""
    if ClapProcessor is None or ClapModel is None or torch is None:
        raise RuntimeError("CLAP model not installed")
    processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
    inputs = processor(audios=samples, sampling_rate=sr, return_tensors="pt")
    with torch.no_grad():
        features = model.get_audio_features(**inputs).squeeze().cpu().numpy()
    return features


__all__ = [
    "load_audio",
    "extract_mfcc",
    "extract_key",
    "extract_tempo",
    "embed_clap",
]

