import sys
import types
import json
from pathlib import Path

# stub heavy optional dependencies
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
dummy_np = types.ModuleType("numpy")
dummy_np.nanmean = lambda a: 0.0
dummy_np.atleast_1d = lambda x: [x]
dummy_np.mean = lambda arr: sum(arr) / len(arr)
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import INANNA_AI.emotional_memory as em


def test_record_and_query(tmp_path, monkeypatch):
    log_file = tmp_path / "emotional_memory.jsonl"
    monkeypatch.setattr(em, "MEMORY_FILE", log_file)
    node = em.EmotionalMemoryNode(
        llm_name="LLM1",
        prompt="hello",
        response="hi",
        emotion="joy",
        success=True,
        archetype="test",
        timestamp="2024-01-01T00:00:00",
    )
    em.record_interaction(node)

    history = em.query_history("LLM1")
    assert len(history) == 1
    assert history[0].prompt == "hello" and history[0].emotion == "joy"


def test_query_filters_and_handles_invalid(tmp_path, monkeypatch):
    log_file = tmp_path / "emotional_memory.jsonl"
    monkeypatch.setattr(em, "MEMORY_FILE", log_file)
    em.record_interaction(
        em.EmotionalMemoryNode(
            llm_name="LLM1",
            prompt="a",
            response="b",
            emotion="calm",
            success=False,
            archetype="arch",
        )
    )
    em.record_interaction(
        em.EmotionalMemoryNode(
            llm_name="LLM2",
            prompt="c",
            response="d",
            emotion="fear",
            success=True,
            archetype="arch",
        )
    )
    # append invalid JSON line
    log_file.write_text(log_file.read_text(encoding="utf-8") + "{\n", encoding="utf-8")

    res = em.query_history("LLM2")
    assert len(res) == 1
    assert res[0].llm_name == "LLM2"


def test_score_affect_defaults(monkeypatch):
    monkeypatch.setattr(em.emotion_analysis, "get_emotion_and_tone", lambda: ("calm", ""))
    monkeypatch.setattr(em.emotion_analysis, "emotion_weight", lambda e: 0.4)
    res = em.score_affect("I love this good day")
    assert res["joy"] > 0
    assert res["trust"] == round(0.4 * (1.0 - res["friction"]), 3)


def test_score_affect_negative(monkeypatch):
    monkeypatch.setattr(em.emotion_analysis, "emotion_weight", lambda e: 0.8)
    res = em.score_affect("bad awful", "stress")
    assert res["joy"] == 0
    assert res["friction"] > 0
    assert res["trust"] == round(0.8 * (1.0 - res["friction"]), 3)


def test_record_interaction_jsonl(tmp_path, monkeypatch):
    log_file = tmp_path / "emotional_memory.jsonl"
    monkeypatch.setattr(em, "MEMORY_FILE", log_file)
    node = em.EmotionalMemoryNode(
        llm_name="LLM3",
        prompt="hey",
        response="sup",
        emotion="neutral",
        success=True,
        archetype="arch",
        timestamp="2024-01-01T00:00:00",
    )
    em.record_interaction(node)
    data = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(data) == 1
    loaded = json.loads(data[0])
    assert loaded["llm_name"] == "LLM3"
    assert loaded["prompt"] == "hey"


def test_score_affect_returns_keys(monkeypatch):
    monkeypatch.setattr(em.emotion_analysis, "get_emotion_and_tone", lambda: ("neutral", ""))
    result = em.score_affect("ok")
    assert set(result) == {"joy", "trust", "friction"}
