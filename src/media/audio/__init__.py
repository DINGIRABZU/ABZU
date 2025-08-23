"""Audio generation and playback interface."""

from __future__ import annotations

from .generation import generate_waveform
from .playback import play_waveform

__all__ = ["generate_waveform", "play_waveform"]
