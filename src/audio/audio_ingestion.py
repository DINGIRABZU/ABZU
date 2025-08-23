from __future__ import annotations

"""Audio ingestion helpers using librosa with optional Essentia and CLAP."""

from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import numpy as np

try:  # pragma: no cover - optional dependency
    import librosa
except Exception:  # pragma: no cover - optional dependency
    # Provide a very small stub so tests can monkeypatch the expected
    # functions without requiring the heavy librosa dependency or its
    # compiled stack.  Any direct use without patching will raise a
    # descriptive error.
    import types

    def _missing(*_a: Any, **_k: Any) -> None:  # pragma: no cover - helper
        raise RuntimeError("librosa library not installed")

    librosa: Any = types.SimpleNamespace(
        load=_missing,
        feature=types.SimpleNamespace(),
        beat=types.SimpleNamespace(tempo=_missing),
    )  # type: ignore[no-redef]

try:  # pragma: no cover - optional dependency
    import essentia.standard as ess
except Exception:  # pragma: no cover - optional dependency
    ess: Any = None  # type: ignore[no-redef]

try:  # pragma: no cover - optional dependency
    import torch

    from transformers import ClapModel, ClapProcessor
except Exception:  # pragma: no cover - optional dependency
    ClapProcessor: Any = None  # type: ignore[no-redef]
    ClapModel: Any = None  # type: ignore[no-redef]
    torch = None


def load_audio(path: Path, sr: int = 44100) -> Tuple[np.ndarray, int]:
    """Load audio using :func:`librosa.load`."""
    if librosa is None:
        raise RuntimeError("librosa library not installed")
    result = librosa.load(path, sr=sr, mono=True)
    return cast(Tuple[np.ndarray, int], result)


def extract_mfcc(samples: np.ndarray, sr: int) -> np.ndarray:
    """Return MFCC features for ``samples``."""
    if librosa is None:
        raise RuntimeError("librosa library not installed")
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
        if librosa is None:
            raise RuntimeError("librosa library not installed")
        tempo = librosa.beat.tempo(y=samples, sr=sr)
        return float(np.atleast_1d(tempo)[0])
    tempo, _ = ess.RhythmExtractor2013(method="multifeature")(samples)
    return float(tempo)


def extract_chroma(samples: np.ndarray, sr: int) -> np.ndarray:
    """Return chroma representation of ``samples``."""
    if librosa is None:
        raise RuntimeError("librosa library not installed")
    return librosa.feature.chroma_cqt(y=samples, sr=sr)


def extract_spectral_centroid(samples: np.ndarray, sr: int) -> np.ndarray:
    """Return spectral centroid of ``samples``."""
    if librosa is None:
        raise RuntimeError("librosa library not installed")
    return librosa.feature.spectral_centroid(y=samples, sr=sr)


def extract_chords(samples: np.ndarray, sr: int) -> List[str]:
    """Estimate chord sequence using simple template matching."""
    if librosa is None:
        raise RuntimeError("librosa library not installed")
    chroma = librosa.feature.chroma_cqt(y=samples, sr=sr)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    major = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], dtype=float)
    minor = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], dtype=float)
    templates: Dict[str, np.ndarray] = {}
    for i, name in enumerate(note_names):
        templates[f"{name}:maj"] = np.roll(major, i)
        templates[f"{name}:min"] = np.roll(minor, i)
    chords: List[str] = []
    for frame in chroma.T:
        scores = {name: float(frame @ tmpl) for name, tmpl in templates.items()}
        best = max(scores, key=lambda name: scores[name])
        chords.append(best)
    return chords


def separate_sources(
    samples: np.ndarray, sr: int, library: str = "spleeter"
) -> Dict[str, np.ndarray]:
    """Separate ``samples`` using Spleeter or Demucs."""
    if library == "spleeter":
        try:  # pragma: no cover - optional dependency
            from spleeter.separator import Separator
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("spleeter library not installed") from exc
        separator = Separator("spleeter:2stems")
        waveform = np.expand_dims(samples, axis=1)
        prediction = separator.separate(waveform)
        return {name: data[:, 0] for name, data in prediction.items()}
    if library == "demucs":
        try:  # pragma: no cover - optional dependency
            import torch
            from demucs.apply import apply_model
            from demucs.pretrained import get_model
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("demucs library not installed") from exc
        model = get_model("htdemucs")
        audio_tensor = torch.tensor(samples).unsqueeze(0).unsqueeze(0)
        with torch.no_grad():
            sources = apply_model(model, audio_tensor, sr=sr)[0]
        return {
            name: src.squeeze().cpu().numpy()
            for name, src in zip(model.sources, sources)
        }
    raise ValueError("library must be 'spleeter' or 'demucs'")


def extract_features(
    path: Path, sr: int = 44100, separate: str | None = None
) -> Dict[str, Any]:
    """Load ``path`` and return a dictionary of audio descriptors."""
    samples, sr = load_audio(path, sr)
    features: Dict[str, Any] = {
        "samples": samples,
        "sr": sr,
        "mfcc": extract_mfcc(samples, sr),
        "key": extract_key(samples),
        "tempo": extract_tempo(samples, sr),
        "chroma": extract_chroma(samples, sr),
        "chords": extract_chords(samples, sr),
        "spectral_centroid": extract_spectral_centroid(samples, sr),
    }
    if separate is not None:
        features["sources"] = separate_sources(samples, sr, separate)
    return features


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
    "extract_chroma",
    "extract_spectral_centroid",
    "extract_chords",
    "separate_sources",
    "extract_features",
    "embed_clap",
]
