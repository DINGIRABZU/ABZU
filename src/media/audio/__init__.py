"""Audio generation and playback interface."""

from __future__ import annotations

from abc import ABC

from ..base import MediaProcessor
from .generation import generate_waveform
from .playback import play_waveform


class AudioProcessor(MediaProcessor, ABC):
    """Base class for audio processors."""


__all__ = ["AudioProcessor", "generate_waveform", "play_waveform"]
