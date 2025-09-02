"""Waveform synthesis utilities."""

from __future__ import annotations

import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

from MUSIC_FOUNDATION import layer_generators


def _note_to_freq_simple(note: str) -> float:
    """Convert a basic note name like ``C4`` to a frequency in Hertz."""

    offsets = {
        "C": -9,
        "C#": -8,
        "Db": -8,
        "D": -7,
        "D#": -6,
        "Eb": -6,
        "E": -5,
        "F": -4,
        "F#": -3,
        "Gb": -3,
        "G": -2,
        "G#": -1,
        "Ab": -1,
        "A": 0,
        "A#": 1,
        "Bb": 1,
        "B": 2,
    }
    name = note[:-1]
    octave = int(note[-1])
    semitone = offsets.get(name, 0) + 12 * (octave - 4)
    return 440.0 * (2 ** (semitone / 12))


def _synthesize_melody(
    tempo: float,
    melody: list[str],
    *,
    wave_type: str = "sine",
    sample_rate: int = 44100,
) -> np.ndarray:
    """Generate a simple waveform for ``melody`` without ``soundfile``."""

    beat_duration = 60.0 / float(tempo)
    segments: list[np.ndarray] = []
    for note in melody:
        freq = _note_to_freq_simple(str(note))
        t = np.linspace(
            0, beat_duration, int(sample_rate * beat_duration), endpoint=False
        )
        if wave_type == "square":
            seg = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
        else:
            seg = 0.5 * np.sin(2 * np.pi * freq * t)
        segments.append(seg.astype(np.float32))
    wave = np.concatenate(segments) if segments else np.zeros(1, dtype=np.float32)
    max_val = float(np.max(np.abs(wave)))
    if max_val > 0:
        wave /= max_val
    return wave.astype(np.float32)


def synthesize(melody: list[str], tempo: float, wave_type: str = "sine") -> np.ndarray:
    """Return a waveform for ``melody`` at ``tempo`` using ``wave_type``."""

    if sf is not None:
        return layer_generators.compose_human_layer(
            tempo, melody, wav_path=None, wave_type=wave_type
        )
    return _synthesize_melody(tempo, melody, wave_type=wave_type)
