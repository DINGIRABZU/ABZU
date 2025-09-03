"""Tests for runtime manager."""

import json
import logging
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml

from agents.razar import health_checks, quarantine_manager as qm
from agents.razar.runtime_manager import RuntimeManager


def test_runtime_manager_resume(failing_runtime, caplog):
    manager, fix_beta, tmp_path, quarantine_dir = failing_runtime

    # First run – beta fails and is quarantined
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert not success
    assert (tmp_path / "alpha.txt").exists()
    assert not (tmp_path / "beta.txt").exists()
    assert not (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "alpha"
    assert state["history"] == ["alpha"]
    assert (quarantine_dir / "beta.json").exists()

    # Second run – fix beta command, reactivate and ensure resume
    fix_beta()
    qm.reactivate_component("beta", verified=True)
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert state["history"] == ["alpha", "beta", "gamma"]
    assert any("Starting component beta" in r.message for r in caplog.records)


def test_runtime_manager_skips_quarantined(failing_runtime, caplog):
    manager, fix_beta, tmp_path, quarantine_dir = failing_runtime

    # First run – beta fails and is quarantined
    manager.run()

    # Second run without reactivation should skip beta
    fix_beta()
    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert not (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads((tmp_path / "run.state").read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert state["history"] == ["alpha", "gamma"]
    assert any(
        "Skipping quarantined component beta" in r.message for r in caplog.records
    )


def _touch_cmd(path: str) -> str:
    return f"python -c \"import pathlib; pathlib.Path('{path}').touch()\""


def test_runtime_manager_health_check_quarantine(tmp_path, monkeypatch):
    quarantine_dir = tmp_path / "quarantine"
    log_file = tmp_path / "log.md"
    monkeypatch.setattr(qm, "QUARANTINE_DIR", quarantine_dir)
    monkeypatch.setattr(qm, "LOG_FILE", log_file)

    module_path = tmp_path / "delta.py"
    module_path.write_text("print('x')", encoding="utf-8")

    config = {
        "components": [
            {
                "name": "delta",
                "priority": 1,
                "command": _touch_cmd(tmp_path / "delta.txt"),
                "module_path": str(module_path),
            }
        ]
    }
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml.safe_dump(config), encoding="utf-8")

    manager = RuntimeManager(
        cfg, state_path=tmp_path / "state.json", venv_path=tmp_path / "venv"
    )
    # Avoid slow environment creation
    monkeypatch.setattr(RuntimeManager, "ensure_venv", lambda self, deps=None: None)

    monkeypatch.setattr(health_checks, "run", lambda name: False)
    success = manager.run()
    assert not success
    # component metadata
    assert (quarantine_dir / "delta.json").exists()
    # module moved
    assert (quarantine_dir / "delta.py").exists()
    meta = json.loads((quarantine_dir / "delta.py.json").read_text(encoding="utf-8"))
    assert meta["reason"] == "health check failed"


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - interface requirement
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:  # pragma: no cover - unused path
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # pragma: no cover - silence server
        return


def _start_health_server(port: int) -> HTTPServer:
    server = HTTPServer(("127.0.0.1", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_launch_servants_reports_endpoints(tmp_path):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = _start_health_server(port)

    root = Path(__file__).resolve().parents[3]
    secrets = root / "secrets.env"
    secrets.write_text(
        f'SERVANT_MODELS="foo=http://127.0.0.1:{port}"\n', encoding="utf-8"
    )

    config = {"components": [{"name": "stub", "priority": 1, "command": "echo stub"}]}
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml.safe_dump(config), encoding="utf-8")

    endpoints = tmp_path / "endpoints.txt"
    env = os.environ | {
        "RAZAR_CONFIG": str(cfg),
        "SERVANT_ENDPOINTS_FILE": str(endpoints),
        "SERVANT_TIMEOUT": "5",
    }

    subprocess.run(
        ["bash", str(root / "launch_servants.sh")], check=True, cwd=root, env=env
    )

    server.shutdown()
    secrets.unlink()

    assert (
        endpoints.read_text(encoding="utf-8").strip() == f"foo=http://127.0.0.1:{port}"
    )
