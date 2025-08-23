"""Avatar generation and playback interface."""

from __future__ import annotations

from abc import ABC

from ..base import MediaProcessor
from . import generation, playback
from .generation import generate_avatar
from .playback import play_avatar


class AvatarProcessor(MediaProcessor, ABC):
    """Base class for avatar processors."""


__all__ = [
    "AvatarProcessor",
    "generate_avatar",
    "play_avatar",
    "generation",
    "playback",
]
