"""Audio playback utilities with optional dependencies."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path


def play_waveform(path: Path) -> None:
    """Play an audio file using ``ffmpeg``.

    Parameters
    ----------
    path:
        Location of the audio file to play.

    Raises
    ------
    ImportError
        If ``ffmpeg`` is not installed.
    """
    try:  # pragma: no cover - dependency guard
        import ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "ffmpeg-python is required for audio playback. Install it via "
            "`pip install ffmpeg-python`."
        ) from exc

    stream = ffmpeg.input(str(path))
    stream = ffmpeg.output(stream, "pipe:", format="wav")
    ffmpeg.run(stream, quiet=True)
