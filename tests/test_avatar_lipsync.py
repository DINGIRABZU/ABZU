from __future__ import annotations

import asyncio
from pathlib import Path
import types

import numpy as np

import video_stream


def test_avatar_lipsync(monkeypatch, tmp_path):
    frames = [np.zeros((4, 4, 3), dtype=np.uint8) for _ in range(4)]
    monkeypatch.setattr(
        video_stream.avatar_expression_engine.video_engine,
        "start_stream",
        lambda lip_sync_audio=None: iter(frames),
    )
    monkeypatch.setattr(
        video_stream.avatar_expression_engine.audio_engine,
        "play_sound",
        lambda path, loop=False: None,
    )
    monkeypatch.setattr(
        video_stream.avatar_expression_engine.emotional_state,
        "get_last_emotion",
        lambda: "neutral",
    )
    monkeypatch.setattr(
        video_stream.avatar_expression_engine,
        "apply_expression",
        lambda frame, emotion: frame,
    )
    wave = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    fake_librosa = types.SimpleNamespace(
        load=lambda *a, **k: (wave, 4),
        beat=types.SimpleNamespace(beat_track=lambda y, sr: (0.0, [])),
    )
    monkeypatch.setattr(video_stream.avatar_expression_engine, "librosa", fake_librosa)

    audio_path = tmp_path / "speech.wav"
    track = video_stream.AvatarVideoTrack(audio_path)

    async def grab() -> tuple[np.ndarray, np.ndarray]:
        first = await track.recv()
        second = await track.recv()
        return first.to_ndarray(), second.to_ndarray()

    frame1, frame2 = asyncio.run(grab())
    assert frame1.sum() > frame2.sum()

