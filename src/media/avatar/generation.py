"""Avatar generation utilities composed from audio and video."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any

from ...lwm import LargeWorldModel

from ..audio import generate_waveform
from ..video import generate_video


def generate_avatar(
    audio_duration_ms: int,
    images: Iterable[Path],
    video_output: Path,
    lwm_model: LargeWorldModel | None = None,
) -> Any:
    """Generate avatar media.

    Parameters
    ----------
    audio_duration_ms:
        Duration for the generated avatar audio segment.
    images:
        Image frames used for the avatar video.
    video_output:
        Path where the rendered video will be written.
    lwm_model:
        Optional :class:`~lwm.LargeWorldModel` used for 3D scene construction
        prior to video rendering.

    Returns
    -------
    Any
        The generated audio segment returned by :func:`generate_waveform`.
    """
    audio_segment = generate_waveform(audio_duration_ms)
    generate_video(list(images), video_output, lwm_model=lwm_model)
    return audio_segment
