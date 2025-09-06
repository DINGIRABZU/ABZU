from __future__ import annotations

import sys
import types
import time

import pytest

# Stub heavy dependencies before importing crown_router
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
dummy_np = types.ModuleType("numpy")
dummy_np.asarray = lambda x, dtype=None: x
dummy_np.linalg = types.SimpleNamespace(norm=lambda x: 1.0)
sys.modules.setdefault("numpy", dummy_np)
qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
qlm_mod.quantum_embed = lambda t: [0.0]
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)
MF = types.ModuleType("MUSIC_FOUNDATION")
MF.qnl_utils = qlm_mod
sys.modules.setdefault("MUSIC_FOUNDATION", MF)

rag_pkg = sys.modules.setdefault("rag", types.ModuleType("rag"))
orch_mod = types.ModuleType("rag.orchestrator")


class DummyOrchestrator:
    def route(self, *a, **k):
        return {"model": "glm"}


orch_mod.MoGEOrchestrator = DummyOrchestrator
rag_pkg.orchestrator = orch_mod
sys.modules["rag.orchestrator"] = orch_mod

doc_mod = types.ModuleType("agents.nazarick.document_registry")

doc_mod.DocumentRegistry = type("DummyRegistry", (), {"get_corpus": lambda self: {}})
sys.modules["agents.nazarick.document_registry"] = doc_mod

crown_decider_mod = types.ModuleType("crown_decider")
crown_decider_mod.decide_expression_options = lambda e: {
    "tts_backend": "",
    "avatar_style": "",
    "aura": None,
}
sys.modules["crown_decider"] = crown_decider_mod

import crown_router
from monitoring.chakra_heartbeat import ChakraHeartbeat


def test_sync_status_alignment() -> None:
    hb = ChakraHeartbeat(chakras=["root", "crown"], window=1.0)
    now = time.time()
    hb.beat("root", now)
    hb.beat("crown", now)
    assert hb.sync_status(now=now + 0.5) == "aligned"
    assert hb.sync_status(now=now + 2.0) == "out_of_sync"


def test_out_of_sync_blocks_crown(monkeypatch) -> None:
    hb = ChakraHeartbeat(chakras=["root", "crown"], window=0.5)
    now = time.time()
    hb.beat("root", now)
    monkeypatch.setattr(crown_router, "heartbeat_monitor", hb)
    monkeypatch.setattr(
        crown_router,
        "decide_expression_options",
        lambda e: {"tts_backend": "", "avatar_style": "", "aura": None},
    )
    with pytest.raises(RuntimeError):
        crown_router.route_decision("hi", {"emotion": "joy"})
