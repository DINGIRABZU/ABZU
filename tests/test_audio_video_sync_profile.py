"""Tests for audio video sync profile."""

from __future__ import annotations

import asyncio
import cProfile
import pstats
import sys
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Ensure optional modules referenced by video_stream are present
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

import video_stream  # noqa: E402


def test_audio_video_sync_with_profile(monkeypatch):
    """Avatar audio and video frames start in sync under profile limits."""

    # Stub video frames to avoid heavy dependencies
    monkeypatch.setattr(
        video_stream.video_engine,
        "generate_avatar_stream",
        lambda: iter([np.zeros((1, 1, 3), dtype=np.uint8)]),
    )

    audio_track = video_stream.AvatarAudioTrack()
    video_track = video_stream.AvatarVideoTrack()

    profiler = cProfile.Profile()
    profiler.enable()
    audio_frame = asyncio.run(audio_track.recv())
    video_frame = asyncio.run(video_track.recv())
    profiler.disable()

    stats = pstats.Stats(profiler)
    assert stats.total_tt < 0.5
    assert audio_frame.pts == 0
    assert video_frame.pts == 0
