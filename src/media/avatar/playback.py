"""Avatar playback utilities."""

from __future__ import annotations

from pathlib import Path

from ..audio import play_waveform
from ..video import play_video


def play_avatar(audio_path: Path, video_path: Path) -> None:
    """Play avatar audio and video streams together."""
    play_waveform(audio_path)
    play_video(video_path)
