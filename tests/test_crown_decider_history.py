import importlib
import sys
from pathlib import Path
import types

dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
dummy_np.mean = lambda arr: sum(arr) / len(arr)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_history_preference(monkeypatch):
    import crown_decider
    importlib.reload(crown_decider)
    monkeypatch.setattr(crown_decider.smm, "list_models", lambda: ["A", "B"])
    monkeypatch.setattr(crown_decider, "_enabled", lambda n: True)
    node_success = crown_decider.emotional_memory.EmotionalMemoryNode(
        llm_name="A",
        prompt="how to",
        response="hi",
        emotion="joy",
        success=True,
        archetype="test",
    )
    node_fail = crown_decider.emotional_memory.EmotionalMemoryNode(
        llm_name="B",
        prompt="how to",
        response="hi",
        emotion="joy",
        success=False,
        archetype="test",
    )
    monkeypatch.setattr(
        crown_decider.emotional_memory,
        "query_history",
        lambda name: [node_success] * 3 if name == "A" else [node_fail] * 3,
    )
    monkeypatch.setattr(
        crown_decider.emotional_memory,
        "score_affect",
        lambda r, e: {"joy": 0.0, "trust": 0.0, "friction": 0.0},
    )
    res = crown_decider.recommend_llm("instructional", "joy")
    assert res == "A"

