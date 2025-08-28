import os
import subprocess
import sys
from pathlib import Path

from agents.razar.ignition_builder import build_ignition


def test_build_ignition(tmp_path: Path) -> None:
    blueprint = tmp_path / "system_blueprint.md"
    blueprint.write_text(
        """
### Alpha
- **Priority:** 1
- **Health Check:** check alpha

### Beta
- **Priority:** 2
- **Health Check:** check beta

## Staged Startup Order
0. Alpha (priority 1)
1. Beta (priority 2)
        """,
        encoding="utf-8",
    )

    output = tmp_path / "Ignition.md"
    build_ignition(blueprint, output)

    content = output.read_text(encoding="utf-8")
    assert "## Priority 1" in content
    assert "## Priority 2" in content
    assert "| 0 | Alpha | check alpha | ⚠️ |" in content
    assert "| 1 | Beta | check beta | ⚠️ |" in content


def test_cli_build_ignition(tmp_path: Path) -> None:
    blueprint = tmp_path / "system_blueprint.md"
    blueprint.write_text(
        """
### Gamma
- **Priority:** 1

## Staged Startup Order
0. Gamma (priority 1)
        """,
        encoding="utf-8",
    )

    output = tmp_path / "Ignition.md"
    cmd = [
        sys.executable,
        "-m",
        "razar",
        "build-ignition",
        "--blueprint",
        str(blueprint),
        "--output",
        str(output),
    ]
    # Inject lightweight stubs for guardian and cocytus via ``sitecustomize`` so
    # the CLI runs without heavy dependencies.
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
    assert "| 0 | Gamma | - | ⚠️ |" in content
