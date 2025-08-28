import json
import os
import subprocess
import sys
import types
from pathlib import Path

# Provide lightweight stubs so importing ``agents.razar`` works without heavy
# dependencies.  These mirror the helpers used in the CLI test but are executed
# at module import time so ``build_ignition`` can be imported safely.
guardian = types.ModuleType("agents.guardian")

def _run_validated_task(*a, **k):
    task = k.get("task")
    return task(*a, **k) if callable(task) else None


guardian.run_validated_task = _run_validated_task
sys.modules.setdefault("agents.guardian", guardian)
cocytus = types.ModuleType("agents.cocytus")
cocytus.__path__ = []
sys.modules.setdefault("agents.cocytus", cocytus)
pa = types.ModuleType("agents.cocytus.prompt_arbiter")

def _arbitrate(*a, **k):
    return None


pa.arbitrate = _arbitrate
sys.modules.setdefault("agents.cocytus.prompt_arbiter", pa)

from agents.razar.ignition_builder import build_ignition


def _write_registry(path: Path) -> None:
    path.write_text(
        (
            "alpha:\n"
            "  priority: P1\n"
            "  criticality: core\n"
            "  issue_type: runtime\n"
            "beta:\n"
            "  priority: P2\n"
            "  criticality: optional\n"
            "  issue_type: config\n"
        ),
        encoding="utf-8",
    )


def test_build_ignition_statuses(tmp_path: Path) -> None:
    registry = tmp_path / "component_priorities.yaml"
    _write_registry(registry)
    state = tmp_path / "razar_state.json"
    state.write_text(json.dumps({"last_component": "alpha"}), encoding="utf-8")

    output = tmp_path / "Ignition.md"
    build_ignition(registry, output, state=state)

    content = output.read_text(encoding="utf-8")
    assert "| 1 | Alpha | - | ✅ |" in content
    assert "| 2 | Beta | - | ⚠️ |" in content


def test_quarantined_component_marked(monkeypatch, tmp_path: Path) -> None:
    registry = tmp_path / "component_priorities.yaml"
    _write_registry(registry)
    output = tmp_path / "Ignition.md"

    monkeypatch.setattr(
        "agents.razar.ignition_builder.quarantine_manager.is_quarantined",
        lambda name: name == "beta",
    )
    build_ignition(registry, output)
    content = output.read_text(encoding="utf-8")
    assert "| 2 | Beta | - | ❌ |" in content


def test_build_ignition_defaults(tmp_path: Path) -> None:
    """When no state is supplied all components default to a warning marker."""

    registry = tmp_path / "component_priorities.yaml"
    _write_registry(registry)
    output = tmp_path / "Ignition.md"
    build_ignition(registry, output)
    content = output.read_text(encoding="utf-8")
    assert "| 1 | Alpha | - | ⚠️ |" in content
    assert "| 2 | Beta | - | ⚠️ |" in content


def test_cli_build_ignition(tmp_path: Path) -> None:
    registry = tmp_path / "component_priorities.yaml"
    _write_registry(registry)
    state = tmp_path / "razar_state.json"
    output = tmp_path / "Ignition.md"

    cmd = [
        sys.executable,
        "-m",
        "razar",
        "build-ignition",
        "--registry",
        str(registry),
        "--state",
        str(state),
        "--output",
        str(output),
    ]

    # Inject lightweight stubs for guardian and cocytus so the CLI imports work.
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    (stubs / "sitecustomize.py").write_text(
        (
            "import sys, types\n"
            "guardian = types.ModuleType('agents.guardian')\n"
            "def run_validated_task(*a, **k):\n"
            "    t=k.get('task')\n"
            "    return t(*a, **k) if callable(t) else None\n"
            "guardian.run_validated_task = run_validated_task\n"
            "sys.modules.setdefault('agents.guardian', guardian)\n"
            "cocytus = types.ModuleType('agents.cocytus')\n"
            "cocytus.__path__ = []\n"
            "sys.modules.setdefault('agents.cocytus', cocytus)\n"
            "pa = types.ModuleType('agents.cocytus.prompt_arbiter')\n"
            "def arbitrate(*a, **k):\n"
            "    return None\n"
            "pa.arbitrate = arbitrate\n"
            "sys.modules.setdefault('agents.cocytus.prompt_arbiter', pa)\n"
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(stubs) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run(cmd, check=True, env=env)

    content = output.read_text(encoding="utf-8")
    assert "| 1 | Alpha | - | ⚠️ |" in content
