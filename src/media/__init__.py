"""Unified media interfaces for audio, video, and avatar."""

from __future__ import annotations

from . import audio, avatar, video
from .base import MediaProcessor

__all__ = ["MediaProcessor", "audio", "avatar", "video"]
