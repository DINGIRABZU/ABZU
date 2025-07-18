from __future__ import annotations

"""Synchronise avatar expressions with audio playback."""

from pathlib import Path
from threading import Thread
from typing import Iterator
import logging

import numpy as np
import librosa

from . import video_engine
from .facial_expression_controller import apply_expression
import audio_engine
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


def stream_avatar_audio(audio_path: Path, fps: int = 15) -> Iterator[np.ndarray]:
    """Yield avatar frames while playing ``audio_path``.

    When ``SadTalker`` or ``wav2lip`` is installed the video engine lip-syncs
    frames directly from the speech sample. Otherwise a simple mouth overlay is
    applied based on audio amplitude.
    """
    wave, sr = librosa.load(str(audio_path), sr=None, mono=True)
    step = max(1, sr // fps)

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
        if not advanced:
            amplitude = float(np.abs(segment).mean())
            frame = apply_expression(frame, emotional_state.get_last_emotion())
            frame = _apply_mouth(frame, amplitude * 10)
        yield frame

    thread.join()


__all__ = ["stream_avatar_audio"]
