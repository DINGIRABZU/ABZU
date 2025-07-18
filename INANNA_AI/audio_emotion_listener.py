from __future__ import annotations

"""Capture microphone audio and estimate the speaker's emotion."""

import logging
from pathlib import Path
from typing import Dict

import numpy as np
import librosa

try:  # pragma: no cover - optional dependency
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency
    sd = None  # type: ignore

import emotional_state

logger = logging.getLogger(__name__)


def record_audio(duration: float, sr: int = 44100) -> np.ndarray:
    """Return ``duration`` seconds of mono audio."""
    if sd is None:
        raise RuntimeError("sounddevice library not installed")
    data = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    return data[:, 0]


def detect_emotion(wave: np.ndarray, sr: int) -> Dict[str, float | str]:
    """Return basic emotion information for ``wave``."""
    if len(wave) == 0:
        return {"emotion": "neutral", "pitch": 0.0, "tempo": 0.0}

    f0 = librosa.yin(wave, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr)
    pitch = float(np.nanmean(f0))
    tempo, _ = librosa.beat.beat_track(y=wave, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    amp = float(np.mean(np.abs(wave)))

    emotion = "neutral"
    if amp > 0.4:
        emotion = "stress"
    elif pitch > 400 and amp < 0.1:
        emotion = "fear"
    elif pitch > 300 and amp > 0.2:
        emotion = "joy"
    elif pitch < 160 and amp < 0.1:
        emotion = "sad"
    elif pitch > 180 and tempo > 120:
        emotion = "excited"
    elif pitch < 120 and tempo < 90:
        emotion = "calm"

    return {"emotion": emotion, "pitch": round(pitch, 2), "tempo": round(tempo, 2)}


def listen_for_emotion(duration: float = 3.0, sr: int = 44100) -> Dict[str, float | str]:
    """Record audio and update :mod:`emotional_state` with the detected emotion."""
    wave = record_audio(duration, sr)
    info = detect_emotion(wave, sr)
    emotional_state.set_last_emotion(info["emotion"])  # type: ignore[arg-type]
    logger.info("detected emotion: %s", info["emotion"])
    return info


__all__ = ["record_audio", "detect_emotion", "listen_for_emotion"]
