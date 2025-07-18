import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import video_engine, context_tracker
import emotional_state


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
