import json
import sys
import types
from pathlib import Path

import pytest


class CrownResponse:
    def __init__(self, acknowledgement="", capabilities=None, downtime=None):
        self.acknowledgement = acknowledgement
        self.capabilities = capabilities or []
        self.downtime = downtime or {}


sys.modules["razar.crown_handshake"] = types.SimpleNamespace(
    perform=lambda path: CrownResponse(),
    CrownResponse=CrownResponse,
)
sys.modules["razar.ai_invoker"] = types.SimpleNamespace(
    handover=lambda name, msg: False
)
sys.modules["razar.doc_sync"] = types.SimpleNamespace(sync_docs=lambda: None)
sys.modules["razar.mission_logger"] = types.SimpleNamespace(
    log_event=lambda *args: None
)
sys.modules["razar.health_checks"] = types.SimpleNamespace(
    run=lambda name: True, CHECKS={}
)
sys.modules["razar.quarantine_manager"] = types.SimpleNamespace(
    is_quarantined=lambda name: False,
    quarantine_component=lambda comp, reason: None,
)
sys.modules["agents.nazarick.service_launcher"] = types.SimpleNamespace(
    launch_required_agents=lambda: None
)

import tests.conftest as conftest_module

conftest_module.ALLOWED_TESTS.add(str(Path(__file__).resolve()))

from razar import boot_orchestrator


def _setup_logs(monkeypatch, tmp_path: Path) -> Path:
    log_dir = tmp_path / "logs"
    monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", log_dir)
    monkeypatch.setattr(boot_orchestrator, "STATE_FILE", log_dir / "razar_state.json")
    monkeypatch.setattr(
        boot_orchestrator, "HISTORY_FILE", log_dir / "razar_boot_history.json"
    )
    return log_dir


def test_boot_sequence_success(monkeypatch, tmp_path):
    log_dir = _setup_logs(monkeypatch, tmp_path)
    config = tmp_path / "boot.json"
    comp = {
        "name": "good_service",
        "command": ["python", "-c", "import time; time.sleep(0.1)"],
        "health_check": ["python", "-c", "import sys; sys.exit(0)"],
    }
    config.write_text(json.dumps({"components": [comp]}))
    components = boot_orchestrator.load_config(config)
    proc = boot_orchestrator.launch_component(components[0])
    proc.wait()
    state = json.loads((log_dir / "razar_state.json").read_text())
    assert state["probes"]["good_service"]["status"] == "ok"


def test_boot_sequence_failure(monkeypatch, tmp_path):
    log_dir = _setup_logs(monkeypatch, tmp_path)
    config = tmp_path / "boot.json"
    comp = {
        "name": "bad_service",
        "command": ["python", "-c", "import time; time.sleep(1)"],
        "health_check": ["python", "-c", "import sys; sys.exit(1)"],
    }
    config.write_text(json.dumps({"components": [comp]}))
    components = boot_orchestrator.load_config(config)
    with pytest.raises(RuntimeError):
        boot_orchestrator.launch_component(components[0])
    state = json.loads((log_dir / "razar_state.json").read_text())
    assert state["probes"]["bad_service"]["status"] == "fail"
