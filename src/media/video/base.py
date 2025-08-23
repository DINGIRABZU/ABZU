"""Video-specific media processing interfaces."""

from __future__ import annotations

from abc import ABC

from ..base import MediaProcessor


class VideoProcessor(MediaProcessor, ABC):
    """Base class for video processors."""


__all__ = ["VideoProcessor"]
