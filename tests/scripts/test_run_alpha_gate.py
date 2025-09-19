from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.conftest import allow_test

allow_test(__file__)


def test_run_alpha_gate_rejects_pytest_addopts() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "PYTEST_ADDOPTS": "-k crown_replay_determinism"}

    result = subprocess.run(
        [
            "bash",
            "scripts/run_alpha_gate.sh",
            "--skip-build",
            "--skip-health",
            "--skip-tests",
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode != 0
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert "Alpha gate disallows pytest -k selectors" in combined_output
