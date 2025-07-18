import sys
import types
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide dummy qnl_utils for vector_memory import
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
ql_mod = types.ModuleType("qnl_utils")
setattr(ql_mod, "quantum_embed", lambda t: [0.0])
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ql_mod)

# Stub heavy orchestrator dependencies before importing module
stub_orch = types.ModuleType("orchestrator")
class StubMoGE:
    def __init__(self):
        pass
stub_orch.MoGEOrchestrator = StubMoGE
sys.modules.setdefault("orchestrator", stub_orch)

import invocation_engine


class DummyOrchestrator:
    def __init__(self):
        self.calls = []

    def mystic(self, symbols, emotion):
        self.calls.append((symbols, emotion))
        return {"hook": symbols}


def test_known_invocation(monkeypatch):
    monkeypatch.setattr(invocation_engine.vector_memory, "add_vector", lambda *a, **k: None)
    invocation_engine.clear_registry()

    called = []

    def cb(sym, emo, orch):
        called.append((sym, emo))
        return "ok"

    invocation_engine.register_invocation("∴⟐+🜂", "joy", cb)

    res = invocation_engine.invoke("∴⟐ + 🜂 [joy]")

    assert res == ["ok"]
    assert called == [("∴⟐+🜂", "joy")]


def test_fuzzy_invocation(monkeypatch):
    invocation_engine.clear_registry()
    monkeypatch.setattr(invocation_engine.vector_memory, "add_vector", lambda *a, **k: None)

    called = []

    def cb(sym, emo, orch):
        called.append((sym, emo))
        return "ok"

    invocation_engine.register_invocation("∴⟐+🜂", "joy", cb)

    def fake_search(query, filter=None, k=1):
        return [{"symbols": "∴⟐+🜂", "emotion": "joy"}]

    monkeypatch.setattr(invocation_engine.vector_memory, "search", fake_search)

    res = invocation_engine.invoke("∴⟐ + 🜄 [joy]")

    assert res == ["ok"]
    assert called == [("∴⟐+🜄", "joy")]


def test_orchestrator_hook(monkeypatch):
    invocation_engine.clear_registry()
    monkeypatch.setattr(invocation_engine.vector_memory, "add_vector", lambda *a, **k: None)

    orch = DummyOrchestrator()
    invocation_engine.register_invocation("∞", None, hook="mystic")

    res = invocation_engine.invoke("∞", orch)

    assert res == [{"hook": "∞"}]
    assert orch.calls == [("∞", None)]


def test_invoke_ritual(monkeypatch, tmp_path, caplog):
    profile = tmp_path / "ritual_profile.json"
    profile.write_text('{"A": {"joy": ["step"]}}', encoding="utf-8")
    monkeypatch.setattr(invocation_engine, "_RITUAL_FILE", profile)
    with caplog.at_level(logging.INFO):
        steps = invocation_engine.invoke_ritual("A")
    assert steps == ["step"]
    assert any("ritual invoked" in r.message for r in caplog.records)


def test_invoke_ritual_list(monkeypatch, tmp_path):
    profile = tmp_path / "ritual_profile.json"
    profile.write_text('{"alist": ["a", "b"]}', encoding="utf-8")
    monkeypatch.setattr(invocation_engine, "_RITUAL_FILE", profile)
    steps = invocation_engine.invoke_ritual("alist")
    assert steps == ["a", "b"]
