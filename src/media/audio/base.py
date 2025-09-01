"""Audio-specific media processing interfaces."""

from __future__ import annotations

__version__ = "0.1.0"

from abc import ABC

from ..base import MediaProcessor


class AudioProcessor(MediaProcessor, ABC):
    """Base class for audio processors."""


__all__ = ["AudioProcessor"]
