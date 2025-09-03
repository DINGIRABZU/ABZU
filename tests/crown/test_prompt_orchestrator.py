"""Tests for crown prompt orchestrator."""

from __future__ import annotations

__version__ = "0.0.0"

import sys
import types
from pathlib import Path
import asyncio

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
dummy_np.mean = lambda arr: sum(arr) / len(arr)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import crown_decider
import servant_model_manager as smm
import crown_prompt_orchestrator as cpo

# Avoid external Neo4j connections during tests
cpo.record_task_flow = lambda *a, **k: None


class DummyGLM:
    def __init__(self):
        self.seen = None

    def complete(self, prompt: str, quantum_context: str | None = None) -> str:
        self.seen = prompt
        return f"glm:{prompt}"


def test_basic_flow(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        cpo,
        "load_interactions",
        lambda limit=3: [{"input": "hi"}],
    )
    result = asyncio.run(cpo.crown_prompt_orchestrator_async("hello", glm))
    assert result["text"].startswith("glm:")
    assert result["model"] == "glm"
    assert "hi" in glm.seen
    assert result["state"] == "dormant"


def test_servant_invocation(monkeypatch):
    glm = DummyGLM()
    smm.register_model("deepseek", lambda p: f"ds:{p}")
    monkeypatch.setattr(crown_decider, "recommend_llm", lambda t, e: "deepseek")
    result = asyncio.run(
        cpo.crown_prompt_orchestrator_async("how do things work?", glm)
    )
    assert result["text"] == "ds:how do things work?"
    assert result["model"] == "deepseek"


def test_servant_failure_falls_back_to_glm(monkeypatch):
    glm = DummyGLM()
    smm.register_model("deepseek", lambda p: f"ds:{p}")
    monkeypatch.setattr(crown_decider, "recommend_llm", lambda t, e: "deepseek")
    monkeypatch.setattr(
        smm, "invoke", lambda name, prompt: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    result = asyncio.run(cpo.crown_prompt_orchestrator_async("oops", glm))
    assert result["model"] == "glm"
    assert result["text"].startswith("glm:")


def test_state_engine_integration(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        cpo,
        "load_interactions",
        lambda limit=3: [],
    )
    result = asyncio.run(cpo.crown_prompt_orchestrator_async("begin the ritual", glm))
    assert result["state"] == "ritual"


def test_empty_interactions_response(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        cpo,
        "load_interactions",
        lambda limit=3: [],
    )
    monkeypatch.setattr(crown_decider, "recommend_llm", lambda t, e: "glm")
    result = asyncio.run(cpo.crown_prompt_orchestrator_async("hello", glm))
    assert result["text"].startswith("glm:")
    assert "<no interactions>" in glm.seen


def test_technical_prefers_kimi(monkeypatch):
    glm = DummyGLM()
    smm._REGISTRY.clear()
    smm.register_model("kimi_k2", lambda p: f"k2:{p}")
    monkeypatch.setattr(
        cpo,
        "load_interactions",
        lambda limit=3: [],
    )
    monkeypatch.setattr(crown_decider, "recommend_llm", lambda t, e: "kimi_k2")
    result = asyncio.run(cpo.crown_prompt_orchestrator_async("import os", glm))
    assert result["text"] == "k2:import os"
    assert result["model"] == "kimi_k2"


def test_reviews_test_metrics(monkeypatch, tmp_path):
    glm = DummyGLM()
    metrics = tmp_path / "pytest_metrics.prom"
    metrics.write_text("pytest_test_failures_total 2\n", encoding="utf-8")
    orig_review = cpo.review_test_outcomes
    monkeypatch.setattr(
        cpo,
        "review_test_outcomes",
        lambda metrics_file=metrics: orig_review(metrics_file),
    )

    logged: list[tuple[str, dict | None]] = []

    def fake_log_suggestion(text, context=None):
        logged.append((text, context))

    monkeypatch.setattr(cpo, "log_suggestion", fake_log_suggestion)
    monkeypatch.setattr(cpo, "load_interactions", lambda limit=3: [])
    monkeypatch.setattr(cpo, "spiral_recall", lambda msg: "")

    result = asyncio.run(cpo.crown_prompt_orchestrator_async("hello", glm))
    assert logged and "2" in logged[0][0]
    assert result["suggestions"] == [logged[0][0]]
