"""Video playback utilities with optional dependencies."""

from __future__ import annotations

from pathlib import Path


def play_video(path: Path) -> None:
    """Play a video file using ``ffmpeg``.

    Parameters
    ----------
    path:
        Location of the video file to play.

    Raises
    ------
    ImportError
        If ``ffmpeg`` is not installed.
    """
    try:  # pragma: no cover - dependency guard
        import ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "ffmpeg-python is required for video playback. Install it via "
            "`pip install ffmpeg-python`."
        ) from exc

    stream = ffmpeg.input(str(path))
    ffmpeg.run(stream, quiet=True)
