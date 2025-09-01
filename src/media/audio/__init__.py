"""Audio generation and playback interface."""

from __future__ import annotations

__version__ = "0.1.0"

from .base import AudioProcessor
from .generation import generate_waveform
from .playback import play_waveform

__all__ = ["AudioProcessor", "generate_waveform", "play_waveform"]
