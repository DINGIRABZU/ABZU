import json
from pathlib import Path

import pytest

from agents.razar import boot_orchestrator as bo
from razar.crown_handshake import CrownResponse

__version__ = "0.1.0"


@pytest.fixture
def stub_handshake(monkeypatch):
    """Stub crown_handshake.perform to return a predefined response."""

    def _stub(response: CrownResponse) -> None:
        async def dummy(brief_path: str) -> CrownResponse:
            assert Path(brief_path).exists()
            return response

        monkeypatch.setattr(bo.crown_handshake, "perform", dummy)

    return _stub


def _basic_orchestrator(tmp_path: Path, monkeypatch) -> bo.BootOrchestrator:
    monkeypatch.setattr(
        bo,
        "parse_system_blueprint",
        lambda _: [{"name": "alpha", "priority": 0, "order": 0, "health_check": None}],
    )
    return bo.BootOrchestrator(
        blueprint=tmp_path / "bp.md",
        config=tmp_path / "cfg.yaml",
        ignition=tmp_path / "Ignition.md",
        state=tmp_path / "razar_state.json",
    )


def test_handshake_archives_and_persists(
    tmp_path: Path, stub_handshake, monkeypatch
) -> None:
    """Mission brief and response files are archived and state captures handshake."""

    orch = _basic_orchestrator(tmp_path, monkeypatch)
    stub_handshake(CrownResponse("ack", ["GLM4V"], {}))
    monkeypatch.setenv("CROWN_WS_URL", "ws://example")
    monkeypatch.setattr(bo.mission_logger, "log_event", lambda *a, **k: None)

    response = orch._perform_handshake()
    orch._persist_handshake(response)

    archive_dir = tmp_path / "mission_briefs"
    files = {p.name for p in archive_dir.glob("*.json")}
    assert any(not name.endswith("_response.json") for name in files)
    assert any(name.endswith("_response.json") for name in files)

    state = json.loads((tmp_path / "razar_state.json").read_text())
    assert state["handshake"]["acknowledgement"] == "ack"


def test_glm4v_launch_logging(tmp_path: Path, monkeypatch) -> None:
    """Missing GLM4V capability triggers launch and archives the event."""

    orch = _basic_orchestrator(tmp_path, monkeypatch)
    monkeypatch.setattr(bo.mission_logger, "log_event", lambda *a, **k: None)

    class DummyResult:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = "ok"

    called: list[list[str]] = []

    def fake_run(cmd, capture_output=False, text=False, check=False):
        called.append(cmd)
        return DummyResult()

    monkeypatch.setattr(bo.subprocess, "run", fake_run)

    orch._ensure_glm4v([])

    assert called, "launcher should run when GLM4V missing"
    archive = list((tmp_path / "mission_briefs").glob("*_glm4v_launch.json"))
    assert archive, "GLM4V launch should be archived"

    state = json.loads((tmp_path / "razar_state.json").read_text())
    assert state["glm4v_present"] is False
    assert "GLM-4.1V" in state["launched_models"]
    assert state["last_model_launch"]["status"] == "success"


def test_glm4v_presence_skips_launch(tmp_path: Path, monkeypatch) -> None:
    """Advertised GLM4V capability prevents launcher execution."""

    orch = _basic_orchestrator(tmp_path, monkeypatch)
    monkeypatch.setattr(bo.mission_logger, "log_event", lambda *a, **k: None)

    called: list[list[str]] = []

    def fake_run(cmd, check=False):  # pragma: no cover - defensive
        called.append(cmd)

    monkeypatch.setattr(bo.subprocess, "run", fake_run)

    orch._ensure_glm4v(["GLM4V"])

    assert not called, "launcher should not run when GLM4V present"
    state = json.loads((tmp_path / "razar_state.json").read_text())
    assert state["glm4v_present"] is True
    assert "launched_models" not in state
    assert "last_model_launch" not in state
