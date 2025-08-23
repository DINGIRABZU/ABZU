"""Video generation and playback interface."""

from __future__ import annotations

from abc import ABC

from ..base import MediaProcessor
from .generation import generate_video
from .playback import play_video


class VideoProcessor(MediaProcessor, ABC):
    """Base class for video processors."""


__all__ = ["VideoProcessor", "generate_video", "play_video"]
