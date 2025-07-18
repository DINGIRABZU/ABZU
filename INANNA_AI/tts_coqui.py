"""Text-to-speech helpers using the Coqui TTS library."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict

import numpy as np

from .utils import save_wav
from .voice_evolution import get_voice_params

try:
    from TTS.api import TTS as CoquiTTS
except ImportError:  # pragma: no cover - optional dependency
    CoquiTTS = None

_model: CoquiTTS | None = None


def _get_tts() -> CoquiTTS:
    """Load and cache the default Coqui TTS model."""
    global _model
    if _model is None:
        if CoquiTTS is None:
            raise RuntimeError("Coqui TTS library not installed")
        _model = CoquiTTS("tts_models/en/vctk/vits")
    return _model


def _sine_placeholder(text: str, style: Dict[str, float], path: Path) -> None:
    """Fallback waveform when Coqui TTS is unavailable."""
    duration = max(1.0, len(text) / 20)
    sr = 22050
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = 220 * (1 + style.get("pitch", 0) * 0.1)
    wave = 0.1 * np.sin(2 * np.pi * freq * t)
    save_wav(wave.astype(np.float32), str(path), sr=sr)


def synthesize_speech(text: str, emotion: str) -> str:
    """Generate speech from ``text`` in a style matching ``emotion``.

    The resulting WAV file path is returned.
    """
    style = get_voice_params(emotion)
    out_path = Path(tempfile.gettempdir()) / f"tts_{abs(hash(text))}.wav"

    if CoquiTTS is not None:
        tts = _get_tts()
        tts.tts_to_file(text=text, file_path=str(out_path), speed=style.get("speed", 1.0))
    else:  # pragma: no cover - optional dependency missing
        _sine_placeholder(text, style, out_path)

    return str(out_path)

__all__ = ["synthesize_speech"]
