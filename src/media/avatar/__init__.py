"""Avatar generation and playback interface."""

from __future__ import annotations

from . import generation, playback
from .generation import generate_avatar
from .playback import play_avatar

__all__ = ["generate_avatar", "play_avatar", "generation", "playback"]
