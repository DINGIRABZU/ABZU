from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.task_profiler import TaskProfiler


def test_classify_task_basic():
    profiler = TaskProfiler()
    assert profiler.classify("how to install package") == "instructional"
    assert profiler.classify("I feel sad") == "emotional"
    assert profiler.classify("what is the meaning of life?") == "philosophical"
    assert profiler.classify("import numpy as np") == "technical"


def test_classify_task_ritual_dict():
    profiler = TaskProfiler()
    assert (
        profiler.classify({"ritual_condition": "☉", "emotion_trigger": "joy"})
        == "ritual"
    )


def test_ritual_action_sequence():
    profiler = TaskProfiler()
    seq = profiler.ritual_action_sequence("☉", "joy")
    assert seq == ["open portal", "weave sound"]
