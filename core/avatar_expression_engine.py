from __future__ import annotations

"""Synchronise avatar expressions with audio playback."""

from pathlib import Path
from threading import Thread
from typing import Iterator
import logging

import numpy as np

try:  # pragma: no cover - optional dependency
    import librosa
except Exception:  # pragma: no cover - optional dependency
    librosa = None  # type: ignore

from . import video_engine
from .facial_expression_controller import apply_expression
from audio import engine as audio_engine
import emotional_state


def _apply_mouth(frame: np.ndarray, ratio: float) -> np.ndarray:
    """Return ``frame`` with a simple mouth overlay based on ``ratio``."""
    result = frame.copy()
    h, w, _ = result.shape
    mouth_h = max(1, h // 8)
    mouth_w = w // 2
    y0 = h - mouth_h
    x0 = (w - mouth_w) // 2
    value = int(max(0.0, min(1.0, ratio)) * 255)
    result[y0 : y0 + mouth_h, x0 : x0 + mouth_w] = value
    return result


def _apply_music_overlay(
    frame: np.ndarray, tempo: float, intensity: float
) -> np.ndarray:
    """Return ``frame`` with tempo and intensity indicators.

    ``tempo`` is expected in beats per minute and is shown as a thin bar along
    the top of the frame. ``intensity`` should be between ``0`` and ``1`` and is
    rendered as a vertical bar on the right edge. The overlay is intentionally
    simple and avoids external imaging dependencies.
    """
    result = frame.copy()
    h, w, _ = result.shape
    tempo_level = int(min(1.0, tempo / 200.0) * 255)
    intensity_level = int(min(1.0, intensity) * 255)
    # Tempo bar across the top
    result[:5, :] = tempo_level
    # Intensity bar down the right side
    result[:, w - 5 :] = intensity_level
    return result


def stream_avatar_audio(audio_path: Path, fps: int = 15) -> Iterator[np.ndarray]:
    """Yield avatar frames while playing ``audio_path``.

    When ``SadTalker`` or ``wav2lip`` is installed the video engine lip-syncs
    frames directly from the speech sample. Otherwise a simple mouth overlay is
    applied based on audio amplitude.
    """
    if librosa is None:
        raise RuntimeError("librosa library not installed")
    wave, sr = librosa.load(str(audio_path), sr=None, mono=True)
    step = max(1, sr // fps)
    try:
        tempo, _ = librosa.beat.beat_track(y=wave, sr=sr)
    except Exception:  # pragma: no cover - tempo extraction is best effort
        tempo = 0.0

    thread = Thread(target=audio_engine.play_sound, args=(audio_path,))
    thread.start()

    advanced = video_engine.SadTalkerPipeline is not None or video_engine.Wav2LipPredictor is not None
    if advanced:
        stream = video_engine.start_stream(lip_sync_audio=audio_path)
    else:
        stream = video_engine.start_stream()

    for start in range(0, len(wave), step):
        try:
            frame = next(stream)
        except StopIteration:
            break
        segment = wave[start : start + step]
        intensity = float(np.sqrt(np.mean(segment ** 2))) if len(segment) else 0.0
        if not advanced:
            amplitude = float(np.abs(segment).mean())
            frame = apply_expression(frame, emotional_state.get_last_emotion())
            frame = _apply_mouth(frame, amplitude * 10)
        frame = _apply_music_overlay(frame, tempo, intensity)
        yield frame

    thread.join()


__all__ = ["stream_avatar_audio"]
