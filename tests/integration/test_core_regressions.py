import types
from pathlib import Path


import pytest

import orchestration_master
import memory_scribe
from memory_store import MemoryStore
from rag.orchestrator import MoGEOrchestrator
import rag.orchestrator as orchestrator_module
from INANNA_AI_AGENT import preprocess

import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))


def test_orchestration_master_boot_sequence_deterministic():
    boot_fn = getattr(orchestration_master, "boot_sequence", None)
    assert callable(boot_fn), "boot_sequence missing"
    first = boot_fn()
    second = boot_fn()
    assert first == second


def test_memory_scribe_store_embedding(monkeypatch):
    calls = []

    class DummyVM:
        def add(self, text):
            calls.append(text)

        def add_vector(self, text, meta):
            calls.append((text, meta))

    monkeypatch.setattr(memory_scribe, "vector_memory", DummyVM())
    memory_scribe.store_embedding("hello")
    assert calls, "embedding not stored"


def test_memory_store_snapshot_and_restore(tmp_path):
    db = tmp_path / "store.sqlite"
    store = MemoryStore(db)
    store.add("abc", [0.1, 0.2], {"k": "v"})
    snap = tmp_path / "snap.sqlite"
    store.snapshot(snap)
    assert snap.exists()
    restored = MemoryStore(tmp_path / "restored.sqlite")
    restored.restore(snap)
    assert restored.ids == ["abc"]
    with pytest.raises(FileNotFoundError):
        restored.restore(tmp_path / "missing.sqlite")


def test_rag_orchestrator_route_audio_failure(monkeypatch, caplog):
    monkeypatch.setattr(
        orchestrator_module.qnl_engine,
        "parse_input",
        lambda text: {"tone": "neutral"},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.symbolic_parser,
        "parse_intent",
        lambda data: [],
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.symbolic_parser,
        "_gather_text",
        lambda data: "",
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.symbolic_parser, "_INTENTS", {}, raising=False
    )
    monkeypatch.setattr(
        orchestrator_module.training_guide,
        "log_result",
        lambda *a, **k: None,
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.archetype_shift_engine,
        "EMOTION_LAYER_MAP",
        {},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.emotional_state,
        "get_last_emotion",
        lambda: "neutral",
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.emotional_state,
        "get_current_layer",
        lambda: None,
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.emotional_state,
        "set_current_layer",
        lambda layer: None,
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.context_tracker,
        "state",
        types.SimpleNamespace(avatar_loaded=False),
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.reflection_loop,
        "load_thresholds",
        lambda: {"default": 1.0},
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module.reflection_loop,
        "run_reflection_loop",
        lambda iterations=1: None,
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "ritual_action_sequence",
        lambda symbols, dom: [],
        raising=False,
    )
    monkeypatch.setattr(
        MoGEOrchestrator, "route", lambda self, text, emotion_data, qnl_data=None: {}
    )
    calls = []
    orch = MoGEOrchestrator()
    monkeypatch.setattr(
        orch._memory_logger,
        "log_ritual_result",
        lambda name, steps: calls.append((name, steps)),
    )

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        orchestrator_module.listening_engine, "analyze_audio", fail, raising=False
    )
    with caplog.at_level("ERROR"):
        result = orch.handle_input("hi")
    assert calls == [("silence_introspection", [])]
    assert "silence introspection failed" in caplog.text
    assert isinstance(result, dict)


def test_inanna_preprocess_cache_warning(tmp_path, caplog):
    cache_dir = tmp_path
    bad_file = cache_dir / "doc.tokens.json"
    bad_file.write_text("not-json", encoding="utf-8")
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            preprocess.preprocess_texts({"doc": "text"}, cache_dir)
    assert f"Failed to read token cache {bad_file}" in caplog.text
