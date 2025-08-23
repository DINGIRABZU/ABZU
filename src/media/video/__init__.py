"""Video generation and playback interface."""

from __future__ import annotations

from .base import VideoProcessor
from .generation import generate_video
from .playback import play_video

__all__ = ["VideoProcessor", "generate_video", "play_video"]
