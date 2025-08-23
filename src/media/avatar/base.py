"""Avatar-specific media processing interfaces."""

from __future__ import annotations

from abc import ABC

from ..base import MediaProcessor


class AvatarProcessor(MediaProcessor, ABC):
    """Base class for avatar processors."""


__all__ = ["AvatarProcessor"]
