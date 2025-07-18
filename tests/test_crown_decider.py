import importlib
import sys
import types
from pathlib import Path

# stub heavy dependencies
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))

dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
dummy_np.mean = lambda arr: sum(arr) / len(arr)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_selection_logic(monkeypatch):
    import crown_decider
    importlib.reload(crown_decider)
    monkeypatch.setattr(crown_decider.smm, "list_models", lambda: ["A", "B"])
    monkeypatch.setattr(crown_decider, "_enabled", lambda n: True)
    monkeypatch.setattr(crown_decider, "classify_task", lambda p: "instructional")
    node_a = crown_decider.emotional_memory.EmotionalMemoryNode(
        llm_name="A",
        prompt="how to",
        response="ok",
        emotion="low",
        success=True,
        archetype="test",
    )
    node_b_success = crown_decider.emotional_memory.EmotionalMemoryNode(
        llm_name="B",
        prompt="how to",
        response="hi",
        emotion="high",
        success=True,
        archetype="test",
    )
    node_b_fail = crown_decider.emotional_memory.EmotionalMemoryNode(
        llm_name="B",
        prompt="how to",
        response="hi",
        emotion="high",
        success=False,
        archetype="test",
    )
    monkeypatch.setattr(
        crown_decider.emotional_memory,
        "query_history",
        lambda name: [node_a] * 3 if name == "A" else [node_b_success, node_b_success, node_b_fail],
    )

    def fake_score(response: str, emotion: str):
        if emotion == "high":
            return {"joy": 0.6, "trust": 0.4, "friction": 0.1}
        return {"joy": 0.0, "trust": 0.2, "friction": 0.0}

    monkeypatch.setattr(crown_decider.emotional_memory, "score_affect", fake_score)
    result = crown_decider.recommend_llm("instructional", "joy")
    assert result == "B"
