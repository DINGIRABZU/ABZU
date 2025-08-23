"""Avatar generation utilities composed from audio and video."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

from ..audio import generate_waveform
from ..video import generate_video


def generate_avatar(audio_duration_ms: int, images: Iterable[Path], video_output: Path) -> Any:
    """Generate avatar media.

    Parameters
    ----------
    audio_duration_ms:
        Duration for the generated avatar audio segment.
    images:
        Image frames used for the avatar video.
    video_output:
        Path where the rendered video will be written.

    Returns
    -------
    Any
        The generated audio segment returned by :func:`generate_waveform`.
    """
    audio_segment = generate_waveform(audio_duration_ms)
    generate_video(list(images), video_output)
    return audio_segment
