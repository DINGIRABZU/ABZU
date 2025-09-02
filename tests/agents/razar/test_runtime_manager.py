"""Tests for runtime manager."""

import json
import logging

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
