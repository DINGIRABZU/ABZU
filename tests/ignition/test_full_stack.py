import json
import sys
import types
from pathlib import Path

import pytest

from razar.crown_handshake import CrownResponse
from agents.nazarick.trust_matrix import TrustMatrix
from agents.operator_dispatcher import OperatorDispatcher
from memory_store import MemoryStore


__version__ = "0.1.0"


def test_full_stack_startup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate full startup path and verify critical subsystems."""

    # avoid heavy imports during boot orchestrator load
    monkeypatch.setitem(sys.modules, "razar.doc_sync", types.ModuleType("doc_sync"))
    monkeypatch.setitem(
        sys.modules, "razar.health_checks", types.ModuleType("health_checks")
    )
    monkeypatch.setitem(sys.modules, "agents.guardian", types.ModuleType("guardian"))
    monkeypatch.setitem(sys.modules, "agents.cocytus", types.ModuleType("cocytus"))

    from razar import boot_orchestrator as bo

    # --- mission brief exchange -------------------------------------------------
    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setenv("CROWN_WS_URL", "ws://example")

    class DummyHandshake:
        def __init__(self, url: str) -> None:  # pragma: no cover - trivial
            self.url = url

        async def perform(self, brief_path: str) -> CrownResponse:
            assert Path(brief_path).exists()
            return CrownResponse("ack", [], {})

    monkeypatch.setattr(bo, "CrownHandshake", DummyHandshake)
    launched: list[list[str]] = []
    monkeypatch.setattr(bo.subprocess, "Popen", lambda cmd: launched.append(cmd))

    result = bo._perform_handshake([{"name": "glm"}])
    assert result.acknowledgement == "ack"
    assert launched, "GLM4V should launch when capability missing"

    archive_dir = tmp_path / "mission_briefs"
    archived = [p for p in archive_dir.glob("*.json") if "_response" not in p.name]
    assert archived, "Archived mission brief not found"

    state = json.loads((tmp_path / "state.json").read_text())
    assert state["capabilities"] == []

    # --- memory initialization ---------------------------------------------------
    store = MemoryStore(tmp_path / "mem.sqlite", snapshot_interval=1)
    store.add("00", [0.1, 0.2, 0.3], {"kind": "test"})
    assert store.search([0.1, 0.2, 0.3], 1)[0][0] == "00"

    # --- agent channels ----------------------------------------------------------
    tm = TrustMatrix(tmp_path / "trust.db")
    assert tm.lookup_protocol("shalltear").startswith("nazarick_rank")
    tm.close()

    # --- operator command routing -----------------------------------------------
    dispatcher = OperatorDispatcher(
        {"overlord": ["crown"]}, log_dir=tmp_path / "ops", worm_dir=tmp_path / "worm"
    )
    res = dispatcher.dispatch("overlord", "crown", lambda: {"ack": "ping"})
    assert res == {"ack": "ping"}
