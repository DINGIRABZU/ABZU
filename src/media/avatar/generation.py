"""Avatar generation utilities composed from audio and video."""

from __future__ import annotations

"""Avatar generation utilities."""

__version__ = "0.1.0"

from pathlib import Path
from typing import Any, Iterable, List, Tuple

from ...lwm import LargeWorldModel
from ..audio import generate_waveform
from ..video import generate_video


def generate_avatar(
    audio_duration_ms: int,
    images: Iterable[Path],
    video_output: Path,
    lwm_model: LargeWorldModel | None = None,
) -> tuple[Any, List[Tuple[float, float, float]]]:
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
    tuple
        A tuple ``(audio_segment, camera_paths)`` where ``audio_segment`` is
        returned by :func:`generate_waveform` and ``camera_paths`` is a list of
        ``(x, y, z)`` coordinates describing the camera trajectory. When no
        ``lwm_model`` is supplied the list is empty.
    """

    image_list = list(images)
    camera_paths: List[Tuple[float, float, float]] = []
    if lwm_model is not None:
        lwm_model.from_frames(image_list)
        camera_paths = [(float(i), 0.0, 0.0) for i in range(len(image_list))]

    audio_segment = generate_waveform(audio_duration_ms)
    generate_video(image_list, video_output, lwm_model=lwm_model)
    return audio_segment, camera_paths
