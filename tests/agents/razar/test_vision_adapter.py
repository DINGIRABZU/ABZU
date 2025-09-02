"""Tests for vision adapter."""

from __future__ import annotations

import numpy as np

from agents.razar.vision_adapter import VisionAdapter
from vision.yoloe_adapter import Detection
from agents.albedo import vision as avatar_vision


def generate_sample() -> "np.ndarray":
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    frame[8:24, 10:22] = 255
    return frame


def test_stream_triggers_plan() -> None:
    frame = generate_sample()
    called = {"count": 0}

    def fake_plan() -> dict:
        called["count"] += 1
        return {"vision_adapter": {"component": "agents.razar.vision_adapter"}}

    adapter = VisionAdapter(module_map={"object": "vision_adapter"}, planner=fake_plan)

    results = list(adapter.stream([frame]))
    assert called["count"] == 1
    assert results[0]["vision_adapter"]["component"] == "agents.razar.vision_adapter"


def test_avatar_updated_from_detections() -> None:
    avatar_vision.consume_detections([])
    adapter = VisionAdapter(planner=lambda: {})
    det = Detection("cat", 1.0, (0, 0, 1, 1))
    adapter.process_detections([det])
    assert avatar_vision.current_avatar() == avatar_vision.AVATAR_MAP["cat"]
