"""Video generation utilities with optional dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def generate_video(images: Iterable[Path], output_path: Path) -> None:
    """Create a video from image frames.

    Parameters
    ----------
    images:
        Iterable of paths to image frames. Currently unused but kept for API
        compatibility.
    output_path:
        Where to write the generated video.

    Raises
    ------
    ImportError
        If ``ffmpeg`` is not installed.
    """
    try:  # pragma: no cover - dependency guard
        import ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "ffmpeg-python is required for video generation. Install it via `pip install ffmpeg-python`."
        ) from exc

    stream = ffmpeg.input(
        "pipe:", format="image2", pattern_type="glob", framerate=24
    )
    stream = ffmpeg.output(stream, str(output_path))
    ffmpeg.run(stream, quiet=True)
