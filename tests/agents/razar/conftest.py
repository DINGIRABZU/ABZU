"""Fixtures for RAZAR runtime tests.

The helpers here simulate component failures so tests can exercise quarantine
and restart behaviour without touching real project paths.
"""

from __future__ import annotations

import sys
import types

import pytest
import yaml

# ``agents.guardian`` and ``agents.cocytus`` perform heavy imports and create a
# circular dependency with ``agents.razar``. Provide minimal stubs so the runtime
# manager can be imported in isolation during tests.
guardian = types.ModuleType("agents.guardian")


def run_validated_task(*args, **kwargs):  # pragma: no cover - test stub
    task = kwargs.get("task")
    return task(*args, **kwargs) if callable(task) else None


guardian.run_validated_task = run_validated_task
sys.modules.setdefault("agents.guardian", guardian)

cocytus_pkg = types.ModuleType("agents.cocytus")
cocytus_pkg.__path__ = []
sys.modules.setdefault("agents.cocytus", cocytus_pkg)

prompt = types.ModuleType("agents.cocytus.prompt_arbiter")


def arbitrate(*_args, **_kwargs):  # pragma: no cover - test stub
    return None


prompt.arbitrate = arbitrate
sys.modules.setdefault("agents.cocytus.prompt_arbiter", prompt)

from agents.razar.runtime_manager import RuntimeManager
import agents.razar.quarantine_manager as qm


def _touch_cmd(path: str) -> str:
    return f"python -c \"import pathlib; pathlib.Path('{path}').touch()\""


@pytest.fixture
def failing_runtime(tmp_path, monkeypatch):
    """Return a runtime manager with a failing component and a fixer."""

    quarantine_dir = tmp_path / "quarantine"
    log_file = tmp_path / "log.md"
    monkeypatch.setattr(qm, "QUARANTINE_DIR", quarantine_dir)
    monkeypatch.setattr(qm, "LOG_FILE", log_file)

    config_path = tmp_path / "razar_config.yaml"
    state_path = tmp_path / "run.state"
    venv_path = tmp_path / "venv"

    beta_fail = "python -c 'import sys; sys.exit(1)'"
    beta_ok = _touch_cmd(tmp_path / "beta.txt")

    config = {
        "components": [
            {
                "name": "alpha",
                "priority": 1,
                "command": _touch_cmd(tmp_path / "alpha.txt"),
            },
            {"name": "beta", "priority": 2, "command": beta_fail},
            {
                "name": "gamma",
                "priority": 3,
                "command": _touch_cmd(tmp_path / "gamma.txt"),
            },
        ]
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manager = RuntimeManager(config_path, state_path=state_path, venv_path=venv_path)

    def fix_beta() -> None:
        config["components"][1]["command"] = beta_ok
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    return manager, fix_beta, tmp_path, quarantine_dir
