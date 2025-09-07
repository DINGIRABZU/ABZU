"""Tests for video."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state
import env_validation
from core import context_tracker, video_engine
from types import SimpleNamespace

pytestmark = pytest.mark.skipif(
    not env_validation.check_audio_binaries(require=False),
    reason="audio tools not installed",
)


def test_generate_one_frame():
    stream = video_engine.start_stream()
    frame = next(stream)
    assert isinstance(frame, np.ndarray)
    assert frame.ndim == 3 and frame.shape[2] == 3


def test_expression_gated_by_avatar(monkeypatch):
    called = {"n": 0}

    def fake_apply(frame, emotion):
        called["n"] += 1
        return frame

    monkeypatch.setattr(video_engine, "apply_expression", fake_apply)
    monkeypatch.setattr(emotional_state, "get_last_emotion", lambda: "joy")
    monkeypatch.setattr(context_tracker.state, "avatar_loaded", False)

    stream = video_engine.start_stream()
    next(stream)
    assert called["n"] == 0


def test_emotion_changes_frame(monkeypatch):
    emotions = iter(["joy", "anger"])
    monkeypatch.setattr(emotional_state, "get_last_emotion", lambda: next(emotions))
    monkeypatch.setattr(context_tracker.state, "avatar_loaded", True)

    stream = video_engine.start_stream()
    frame1 = next(stream)
    frame2 = next(stream)
    assert np.any(frame1 != frame2)


def test_upscaled_output(monkeypatch):
    monkeypatch.setattr(context_tracker.state, "avatar_loaded", False)
    stream = video_engine.start_stream(scale=2)
    frame = next(stream)
    assert frame.shape[0] == 128 and frame.shape[1] == 128


def test_camera_paths_highlight_pixel(monkeypatch):
    """Camera paths from LWM should influence rendered frames."""
    dummy = SimpleNamespace(inspect_scene=lambda: {"points": [{"index": 0}]})
    monkeypatch.setattr(video_engine, "default_lwm", dummy)
    stream = video_engine.generate_avatar_stream()
    frame = next(stream)
    assert np.array_equal(frame[0, 0], np.array([255, 0, 0], dtype=np.uint8))
