from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from task_profiling import classify_task, ritual_action_sequence


def test_classify_task_basic():
    assert classify_task("how to install package") == "instructional"
    assert classify_task("I feel sad") == "emotional"
    assert classify_task("what is the meaning of life?") == "philosophical"
    assert classify_task("import numpy as np") == "technical"


def test_classify_task_ritual_dict():
    assert classify_task({"ritual_condition": "☉", "emotion_trigger": "joy"}) == "ritual"


def test_ritual_action_sequence():
    seq = ritual_action_sequence("☉", "joy")
    assert seq == ["open portal", "weave sound"]
