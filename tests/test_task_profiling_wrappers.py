import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import task_profiling as tp
from core.task_profiler import TaskProfiler


def test_classify_and_ritual_sequence(monkeypatch):
    profile = {"sleep": {"tired": ["rest"]}}
    monkeypatch.setattr(tp, "_profiler", TaskProfiler(ritual_profile=profile))
    assert tp.classify_task("how to bake") == "instructional"
    assert tp.classify_task({"text": "I feel joy"}) == "emotional"
    assert tp.classify_task({"ritual_condition": "sleep", "emotion_trigger": "tired"}) == "ritual"
    assert tp.ritual_action_sequence("sleep", "tired") == ["rest"]
