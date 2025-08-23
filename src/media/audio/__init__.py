"""Audio generation and playback interface."""

from .generation import generate_waveform
from .playback import play_waveform

__all__ = ["generate_waveform", "play_waveform"]
