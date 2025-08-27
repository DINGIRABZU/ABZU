import json
import logging

import yaml

from agents.razar.runtime_manager import RuntimeManager


def _touch_cmd(filename: str) -> str:
    return f"python -c \"import pathlib; pathlib.Path('{filename}').touch()\""


def _write_exec_cmd(filename: str) -> str:
    return (
        "python -c \"import pathlib,sys; "
        f"pathlib.Path('{filename}').write_text(sys.executable)\""
    )


def test_runtime_manager_resume(tmp_path, caplog):
    config_path = tmp_path / "razar_config.yaml"
    state_path = tmp_path / "run.state"
    venv_path = tmp_path / "venv"

    config = {
        "components": [
            {"name": "beta", "priority": 2, "command": _touch_cmd("beta.txt")},
            {"name": "alpha", "priority": 1, "command": _write_exec_cmd("alpha.txt")},
            {"name": "gamma", "priority": 3, "command": _touch_cmd("gamma.txt")},
        ]
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manager = RuntimeManager(config_path, state_path=state_path, venv_path=venv_path)

    # First run – alpha succeeds, beta fails, gamma skipped
    config["components"][0]["command"] = "python -c 'import sys; sys.exit(1)'"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert not success
    assert (tmp_path / "alpha.txt").exists()
    assert not (tmp_path / "beta.txt").exists()
    assert not (tmp_path / "gamma.txt").exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_component"] == "alpha"
    exec_path = (tmp_path / "alpha.txt").read_text(encoding="utf-8")
    assert str(venv_path) in exec_path

    # Second run – fix beta command and ensure resume
    config["components"][0]["command"] = _touch_cmd("beta.txt")
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with caplog.at_level(logging.INFO):
        success = manager.run()
    assert success
    assert (tmp_path / "beta.txt").exists()
    assert (tmp_path / "gamma.txt").exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_component"] == "gamma"
    assert any("Starting component beta" in r.message for r in caplog.records)
