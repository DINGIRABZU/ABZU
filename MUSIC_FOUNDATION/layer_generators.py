#!/usr/bin/env python3
"""Basic waveform generators for Spiral OS music layers.

The main entry point `compose_human_layer` builds a simple melodic layer from
``tempo`` and ``melody`` inputs. Notes may be provided as names (e.g. ``"C4"``)
or numeric frequencies in Hertz. The function writes a WAV file called
``human_layer.wav`` by default and returns the synthesized waveform.
"""

from __future__ import annotations

import os
from typing import Sequence, Union

import librosa
import numpy as np
import soundfile as sf

NoteLike = Union[str, float, int]


def _note_to_freq(note: NoteLike) -> float:
    """Convert a note specification to a frequency in Hz."""
    if isinstance(note, (float, int)):
        return float(note)
    return float(librosa.note_to_hz(str(note)))


def compose_human_layer(
    tempo: float,
    melody: Sequence[NoteLike],
    *,
    sample_rate: int = 44100,
    wav_path: str | None = "human_layer.wav",
    wave_type: str = "sine",
) -> np.ndarray:
    """Synthesize a simple melody and optionally write it to ``wav_path``."""

    if not melody:
        return np.zeros(1, dtype=np.float32)

    beat_duration = 60.0 / float(tempo)
    segments = []
    for note in melody:
        freq = _note_to_freq(note)
        t = np.arange(int(beat_duration * sample_rate)) / sample_rate
        if wave_type == "square":
            seg = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
        else:
            seg = 0.5 * np.sin(2 * np.pi * freq * t)
        segments.append(seg.astype(np.float32))

    wave = np.concatenate(segments)
    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave = wave / max_val

    if wav_path:
        os.makedirs(os.path.dirname(wav_path) or ".", exist_ok=True)
        sf.write(wav_path, wave, sample_rate)
    return wave


def generate_tone(frequency: float, duration: float, *, sample_rate: int = 44100) -> np.ndarray:
    """Return a normalized sine tone for ``duration`` seconds."""

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.1 * np.sin(2 * np.pi * frequency * t)
    return tone.astype(np.float32)


def add_crystal_layer(
    base_waveform: np.ndarray,
    *,
    sample_rate: int = 44100,
    tones: Sequence[float] = (432.0, 528.0),
    wav_path: str | None = None,
) -> np.ndarray:
    """Overlay subtle crystal tones onto ``base_waveform``."""

    duration = base_waveform.size / sample_rate
    overlay = np.zeros_like(base_waveform)
    for freq in tones:
        tone = generate_tone(freq, duration, sample_rate=sample_rate)
        if tone.size < overlay.size:
            tone = np.pad(tone, (0, overlay.size - tone.size))
        overlay += tone[: overlay.size]

    combined = base_waveform.astype(np.float32) + overlay
    max_val = np.max(np.abs(combined))
    if max_val > 0:
        combined /= max_val

    if wav_path:
        os.makedirs(os.path.dirname(wav_path) or ".", exist_ok=True)
        sf.write(wav_path, combined, sample_rate)

    return combined
