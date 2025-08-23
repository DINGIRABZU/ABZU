"""Video generation utilities with optional dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ...lwm import LargeWorldModel


def generate_video(
    images: Iterable[Path],
    output_path: Path,
    lwm_model: LargeWorldModel | None = None,
) -> None:
    """Create a video from image frames with optional 3D scene generation.

    Parameters
    ----------
    images:
        Iterable of paths to image frames. Currently unused but kept for API
        compatibility.
    output_path:
        Where to write the generated video.
    lwm_model:
        Optional :class:`~lwm.LargeWorldModel` instance used to build a 3D
        representation from ``images`` before rendering the video.

    Raises
    ------
    ImportError
        If ``ffmpeg`` is not installed.
    """
    if lwm_model:
        images = list(images)
        lwm_model.from_frames(images)

    try:  # pragma: no cover - dependency guard
        import ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "ffmpeg-python is required for video generation. Install it via `pip install ffmpeg-python`."
        ) from exc

    stream = ffmpeg.input("pipe:", format="image2", pattern_type="glob", framerate=24)
    stream = ffmpeg.output(stream, str(output_path))
    ffmpeg.run(stream, quiet=True)
