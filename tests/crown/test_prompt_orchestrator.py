"""Tests for crown prompt orchestrator."""

from __future__ import annotations

__version__ = "0.0.0"

import sys
import types
from pathlib import Path
import asyncio
import hashlib
import pytest

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
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
import INANNA_AI.glm_integration as gi

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


def test_deterministic_ids(monkeypatch):
    """Stable IDs and symbols derive from SHA256 of the message."""
    glm = DummyGLM()
    captured: dict[str, str] = {}

    def fake_record_task_flow(identifier, _data):
        captured["id"] = identifier

    monkeypatch.setattr(cpo, "record_task_flow", fake_record_task_flow)
    monkeypatch.setattr(cpo, "load_interactions", lambda limit=3: [])

    message = "hello"
    result = asyncio.run(cpo.crown_prompt_orchestrator_async(message, glm))

    stable_hash = hashlib.sha256(message.encode()).hexdigest()
    assert captured["id"] == f"msg_{stable_hash}"

    symbols = [
        "☉",
        "☾",
        "⚚",
        "♇",
        "♈",
        "♉",
        "♊",
        "♋",
        "♌",
        "♍",
        "♎",
        "♏",
        "♐",
        "♑",
        "♒",
        "♓",
    ]
    expected_symbol = symbols[int(stable_hash, 16) % len(symbols)]
    assert result["symbol"] == expected_symbol


def test_glm_health_check_success(monkeypatch):
    """``GLMIntegration`` probes the endpoint during initialization."""
    called = {}

    class DummyResp:
        def raise_for_status(self) -> None:
            pass

    def fake_get(url, timeout, headers=None):
        called["url"] = url
        return DummyResp()

    monkeypatch.setattr(gi.requests, "get", fake_get)
    gi.GLMIntegration(endpoint="https://glm.example.com")
    assert called["url"].endswith("/health")


def test_glm_health_check_failure(monkeypatch):
    """Initialization fails fast when the endpoint is unreachable."""

    def fake_get(url, timeout, headers=None):
        raise gi.requests.RequestException("boom")

    monkeypatch.setattr(gi.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        gi.GLMIntegration(endpoint="https://glm.example.com")


def test_cli_entry(monkeypatch, capsys):
    """CLI ``main`` prints the orchestrator result."""

    def fake_orchestrator(message, glm):
        return {"text": f"resp:{message}"}

    class DummyMainGLM:
        def __init__(self, endpoint=None, api_key=None, temperature=0.8):
            pass

    monkeypatch.setattr(cpo, "crown_prompt_orchestrator", fake_orchestrator)
    monkeypatch.setattr(cpo, "GLMIntegration", DummyMainGLM)

    cpo.main(["hello"])
    out = capsys.readouterr().out
    assert out.strip() == "resp:hello"
