"""Integration tests for manifesto-based validation."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

otel = types.ModuleType("opentelemetry")
otel.trace = types.SimpleNamespace(get_tracer=lambda *a, **k: None)
sys.modules.setdefault("opentelemetry", otel)

from agents.nazarick.ethics_manifesto import LAWS
from INANNA_AI.ethical_validator import EthicalValidator


def test_validator_uses_manifesto_laws():
    validator = EthicalValidator()
    first = LAWS[0]
    result = validator.validate_action(
        "Ainz", f"prepare to {first.keywords[0]} the village"
    )
    assert not result["compliant"]
    assert first.name in result["violated_laws"]


def test_crown_router_blocks_violations(monkeypatch):
    sys.modules.setdefault("librosa", types.ModuleType("librosa"))
    sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
    sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
    dummy_np = types.ModuleType("numpy")
    dummy_np.asarray = lambda x, dtype=None: x
    dummy_np.linalg = types.SimpleNamespace(norm=lambda x: 1.0)
    sys.modules.setdefault("numpy", dummy_np)
    qnl_utils = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
    qnl_utils.quantum_embed = lambda t: [0.0]
    mf = types.ModuleType("MUSIC_FOUNDATION")
    mf.qnl_utils = qnl_utils
    sys.modules.setdefault("MUSIC_FOUNDATION", mf)
    sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qnl_utils)

    rag_pkg = sys.modules.setdefault("rag", types.ModuleType("rag"))
    orch_mod = types.ModuleType("rag.orchestrator")

    class DummyOrchestrator:
        def route(self, *a, **k):
            return {"model": "glm"}

    orch_mod.MoGEOrchestrator = DummyOrchestrator
    rag_pkg.orchestrator = orch_mod
    sys.modules.setdefault("rag.orchestrator", orch_mod)

    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    import crown_router

    importlib.reload(crown_router)

    monkeypatch.setattr(
        crown_router, "vector_memory", types.SimpleNamespace(search=lambda *a, **k: [])
    )
    monkeypatch.setattr(crown_router, "decide_expression_options", lambda e: {})
    monkeypatch.setattr(crown_router.emotional_state, "get_soul_state", lambda: "")

    validator = EthicalValidator()
    with pytest.raises(ValueError):
        crown_router.route_decision(
            "prepare to attack the village", {"emotion": "neutral"}, validator=validator
        )
