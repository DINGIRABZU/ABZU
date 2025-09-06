"""Integration tests for the document registry."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

otel = types.ModuleType("opentelemetry")
otel.trace = types.SimpleNamespace(get_tracer=lambda *a, **k: None)
sys.modules.setdefault("opentelemetry", otel)

from agents.nazarick.document_registry import DocumentRegistry


def test_registry_collects_expected_files():
    registry = DocumentRegistry([Path("GENESIS"), Path("IGNITION")])
    corpus = registry.get_corpus()
    names = {Path(p).name for p in corpus}
    assert "GENESIS_.md" in names
    assert "EA_ENUMA_ELISH_.md" in names


def test_crown_router_receives_documents(monkeypatch):
    sys.modules.setdefault("librosa", types.ModuleType("librosa"))
    sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
    sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
    dummy_np = types.ModuleType("numpy")
    dummy_np.asarray = lambda x, dtype=None: x
    dummy_np.linalg = types.SimpleNamespace(norm=lambda x: 1.0)
    sys.modules.setdefault("numpy", dummy_np)
    audio_mod = types.ModuleType("audio")
    audio_mod.voice_aura = types.SimpleNamespace()
    sys.modules.setdefault("audio", audio_mod)
    qnl_utils = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
    qnl_utils.quantum_embed = lambda t: [0.0]
    mf = types.ModuleType("MUSIC_FOUNDATION")
    mf.qnl_utils = qnl_utils
    sys.modules.setdefault("MUSIC_FOUNDATION", mf)
    sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qnl_utils)

    docs_seen: dict[str, dict[str, str] | None] = {}

    class DummyOrchestrator:
        def route(
            self,
            text,
            emotion_data,
            *,
            text_modality=False,
            voice_modality=False,
            music_modality=False,
            documents=None,
        ):
            docs_seen["docs"] = documents
            return {"model": "glm"}

    rag_pkg = sys.modules.setdefault("rag", types.ModuleType("rag"))
    orch_mod = types.ModuleType("rag.orchestrator")
    orch_mod.MoGEOrchestrator = DummyOrchestrator
    rag_pkg.orchestrator = orch_mod
    sys.modules.setdefault("rag.orchestrator", orch_mod)

    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

    import crown_router

    importlib.reload(crown_router)

    registry = DocumentRegistry([Path("GENESIS"), Path("IGNITION")])
    monkeypatch.setattr(crown_router, "registry", registry)
    monkeypatch.setattr(
        crown_router, "vector_memory", types.SimpleNamespace(search=lambda *a, **k: [])
    )
    monkeypatch.setattr(crown_router, "decide_expression_options", lambda e: {})
    monkeypatch.setattr(crown_router.emotional_state, "get_soul_state", lambda: "")

    crown_router.route_decision("hi", {"emotion": "joy"})
    assert docs_seen["docs"]
