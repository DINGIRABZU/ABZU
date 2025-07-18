import importlib
import sys
import time
import types
from pathlib import Path

# stub heavy dependencies
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_failure_rotation(monkeypatch):
    monkeypatch.setenv("LLM_ROTATION_PERIOD", "1")
    monkeypatch.setenv("LLM_MAX_FAILURES", "2")
    import crown_decider
    importlib.reload(crown_decider)
    monkeypatch.setattr(crown_decider.smm, "has_model", lambda name: True)
    monkeypatch.setattr(crown_decider.smm, "list_models", lambda: ["deepseek"]) 
    sample = [
        crown_decider.emotional_memory.EmotionalMemoryNode(
            llm_name="deepseek",
            prompt="how to",
            response="ok",
            emotion="neutral",
            success=True,
            archetype="test",
        )
    ] * 3
    monkeypatch.setattr(
        crown_decider.emotional_memory,
        "query_history",
        lambda name: sample,
    )

    crown_decider.record_result("deepseek", False)
    crown_decider.record_result("deepseek", False)
    assert crown_decider.recommend_llm("instructional", "neutral") == "glm"

    time.sleep(1.1)
    assert crown_decider.recommend_llm("instructional", "neutral") == "deepseek"


def test_time_based_rotation(monkeypatch):
    monkeypatch.setenv("LLM_ROTATION_PERIOD", "1")
    monkeypatch.setenv("LLM_MAX_FAILURES", "5")
    import crown_decider
    importlib.reload(crown_decider)
    monkeypatch.setattr(crown_decider.smm, "list_models", lambda: ["deepseek"])
    sample = [
        crown_decider.emotional_memory.EmotionalMemoryNode(
            llm_name="deepseek",
            prompt="how to",
            response="ok",
            emotion="neutral",
            success=True,
            archetype="test",
        )
    ] * 3
    monkeypatch.setattr(
        crown_decider.emotional_memory,
        "query_history",
        lambda name: sample,
    )

    crown_decider.record_result("deepseek", True)
    time.sleep(1.1)
    crown_decider.record_result("deepseek", True)
    assert crown_decider.recommend_llm("instructional", "neutral") == "glm"

    time.sleep(1.1)
    assert crown_decider.recommend_llm("instructional", "neutral") == "deepseek"
