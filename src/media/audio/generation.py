"""Audio generation utilities with optional dependencies."""

from __future__ import annotations

from typing import Any


def generate_waveform(duration_ms: int, freq: int = 440) -> Any:
    """Generate a sine wave audio segment.

    Parameters
    ----------
    duration_ms:
        Length of the waveform in milliseconds.
    freq:
        Frequency of the sine wave in Hertz.

    Returns
    -------
    Any
        A ``pydub.AudioSegment`` representing the waveform.

    Raises
    ------
    ImportError
        If the optional dependency ``pydub`` is not installed.
    """
    try:  # pragma: no cover - dependency guard
        from pydub import AudioSegment
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "pydub is required for audio generation. Install it via `pip install pydub`."
        ) from exc

    segment = AudioSegment.sine(duration=duration_ms, frequency=freq)
    return segment
