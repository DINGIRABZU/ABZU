import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_feedback_loop as afl
import cortex_memory
import archetype_shift_engine


def test_clustered_emotions(monkeypatch):
    mem = [
        {"decision": {"emotion": "anger", "event": "hi"}},
        {"decision": {"emotion": "anger", "event": "hello"}},
        {"decision": {"emotion": "anger", "event": "bye"}},
    ]
    monkeypatch.setattr(cortex_memory, "query_spirals", lambda: mem)
    called = {}

    def fake_shift(event, emotion):
        called["args"] = (event, emotion)
        return "nigredo_layer"

    monkeypatch.setattr(archetype_shift_engine, "maybe_shift_archetype", fake_shift)

    res = afl.evaluate_archetype()

    assert res == "nigredo_layer"
    assert called["args"] == ("bye", "anger")


def test_repeated_sigil(monkeypatch):
    mem = [
        {"decision": {"emotion": "joy", "event": "begin ☉"}},
        {"decision": {"emotion": "calm", "event": "continue ☉"}},
    ]
    monkeypatch.setattr(cortex_memory, "query_spirals", lambda: mem)
    called = {}

    def fake_shift(event, emotion):
        called["args"] = (event, emotion)
        return "citrinitas_layer"

    monkeypatch.setattr(archetype_shift_engine, "maybe_shift_archetype", fake_shift)

    res = afl.evaluate_archetype()

    assert res == "citrinitas_layer"
    # should detect repeated sigil and dominant emotion "calm"
    assert called["args"] == ("☉", "calm")


def test_empty_memory(monkeypatch):
    monkeypatch.setattr(cortex_memory, "query_spirals", lambda: [])
    res = afl.evaluate_archetype()
    assert res is None
