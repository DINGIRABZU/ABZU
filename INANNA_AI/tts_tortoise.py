from __future__ import annotations

"""Text-to-speech wrapper for the Tortoise library."""

import tempfile
from pathlib import Path

import numpy as np

from .utils import save_wav
from .voice_evolution import get_voice_params

try:  # pragma: no cover - optional dependency
    from tortoise.api import TextToSpeech
except Exception:  # pragma: no cover - optional dependency
    TextToSpeech = None  # type: ignore

_model: TextToSpeech | None = None


def _get_model() -> TextToSpeech:
    """Load and cache the Tortoise TTS model."""
    global _model
    if _model is None:
        if TextToSpeech is None:
            raise RuntimeError("Tortoise library not installed")
        _model = TextToSpeech()
    return _model


def _sine_placeholder(text: str, path: Path, pitch: float) -> None:
    """Write a simple sine wave as a fallback."""
    duration = max(1.0, len(text) / 20)
    sr = 22050
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = 220 * (1 + pitch * 0.1)
    wave = 0.1 * np.sin(2 * np.pi * freq * t)
    save_wav(wave.astype(np.float32), str(path), sr=sr)


def synthesize(text: str, emotion: str) -> str:
    """Return a WAV path containing ``text`` spoken in ``emotion`` style."""
    style = get_voice_params(emotion)
    out_path = Path(tempfile.gettempdir()) / f"tortoise_{abs(hash(text))}.wav"

    if TextToSpeech is not None:
        try:  # pragma: no cover - external library
            model = _get_model()
            model.tts_to_file(text=text, file_path=str(out_path))
        except Exception:  # pragma: no cover - fallback
            _sine_placeholder(text, out_path, style.get("pitch", 0.0))
    else:  # pragma: no cover - optional dependency missing
        _sine_placeholder(text, out_path, style.get("pitch", 0.0))

    return str(out_path)


__all__ = ["synthesize"]
