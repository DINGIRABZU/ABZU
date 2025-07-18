import sys
from pathlib import Path
import types

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

dummy_vm = types.ModuleType("vector_memory")
sys.modules.setdefault("vector_memory", dummy_vm)
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))

from tools import reflection_loop
from core import video_engine
import corpus_memory_logging


def test_citrinitas_ritual_invoked(monkeypatch):
    frames = iter([np.zeros((1, 1, 3), dtype=np.uint8) for _ in range(3)])
    monkeypatch.setattr(video_engine, "start_stream", lambda: frames)
    monkeypatch.setattr(reflection_loop, "detect_expression", lambda f: "citrinitas")
    monkeypatch.setattr(reflection_loop, "load_thresholds", lambda: {"citrinitas": 2})
    monkeypatch.setattr(reflection_loop, "cv2", None)
    monkeypatch.setattr(reflection_loop.adaptive_learning, "update_mirror_thresholds", lambda r: None)

    called = {}

    def fake_invoke(name):
        called["ritual"] = name
        return ["step"]

    def fake_log(name, steps):
        called["steps"] = steps

    monkeypatch.setattr(reflection_loop, "invoke_ritual", fake_invoke)
    monkeypatch.setattr(reflection_loop, "log_ritual_result", fake_log)

    reflection_loop.run_reflection_loop(iterations=3)

    assert called["ritual"] == "citrinitas_rite"
    assert called["steps"] == ["step"]
