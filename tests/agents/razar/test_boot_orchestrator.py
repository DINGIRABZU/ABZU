"""Tests for boot orchestrator."""

import json
from pathlib import Path

import pytest

from razar import boot_orchestrator as bo
from razar.crown_handshake import CrownResponse

__version__ = "0.1.0"


@pytest.fixture
def mock_handshake(monkeypatch):
    """Stub out ``crown_handshake.perform`` to avoid network calls."""

    def _mock(response: CrownResponse):
        async def dummy(brief_path: str) -> CrownResponse:
            assert Path(brief_path).exists()
            return response

        monkeypatch.setattr(bo.crown_handshake, "perform", dummy)

    return _mock


def test_perform_handshake_persists_state_and_launches_model(
    tmp_path: Path, mock_handshake, monkeypatch
) -> None:
    """Handshake results are stored and missing capability triggers launcher."""

    monkeypatch.setattr(bo, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(bo, "STATE_FILE", tmp_path / "razar_state.json")
    monkeypatch.setenv("CROWN_WS_URL", "ws://example")

    response = CrownResponse("ack", [], {})
    mock_handshake(response)

    launched: list[list[str]] = []
    monkeypatch.setattr(bo.subprocess, "Popen", lambda cmd: launched.append(cmd))

    result = bo._perform_handshake([{"name": "alpha"}])

    assert result == response
    assert launched, "crown model should launch when GLM4V missing"
    state = json.loads((tmp_path / "razar_state.json").read_text())
    assert state == {"capabilities": [], "downtime": {}}


def test_finalize_metrics_updates_history(monkeypatch) -> None:
    """Finalize metrics computes success rate and persists history."""

    history: dict = {"history": [], "best_sequence": None, "component_failures": {}}
    run_metrics = {
        "timestamp": 0,
        "components": [
            {"name": "a", "success": True},
            {"name": "b", "success": False},
        ],
    }
    saved: dict = {}
    monkeypatch.setattr(bo, "save_history", lambda data: saved.update(data))
    monkeypatch.setattr(bo.time, "time", lambda: 1)

    bo.finalize_metrics(run_metrics, history, {"b": 1}, start_time=0)

    assert run_metrics["success_rate"] == 0.5
    assert run_metrics["total_time"] == 1
    assert history["best_sequence"]["components"] == ["a"]
    assert saved["component_failures"]["b"] == 1
