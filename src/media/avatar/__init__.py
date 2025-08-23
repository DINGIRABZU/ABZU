"""Avatar generation and playback interface."""

from __future__ import annotations

from . import generation, playback
from .base import AvatarProcessor
from .generation import generate_avatar
from .playback import play_avatar

__all__ = ["AvatarProcessor", "generate_avatar", "play_avatar", "generation", "playback"]
