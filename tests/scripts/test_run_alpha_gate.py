from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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


def test_run_alpha_gate_fails_when_coverage_export_errors(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir(parents=True, exist_ok=True)

    real_python = sys.executable
    python_stub = stub_dir / "python"
    python_stub.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$1" == "scripts/export_coverage.py" ]]; then\n'
        "  echo 'simulated export failure' >&2\n"
        "  exit 123\n"
        "fi\n"
        f'exec "{real_python}" "$@"\n',
        encoding="utf-8",
    )
    python_stub.chmod(0o755)

    pytest_stub = stub_dir / "pytest"
    pytest_stub.write_text(
        "#!/usr/bin/env bash\n" "echo 'stub pytest execution' >&2\n" "exit 0\n",
        encoding="utf-8",
    )
    pytest_stub.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}",
    }

    summary_path = repo_root / "monitoring" / "alpha_gate_summary.json"
    prom_path = repo_root / "monitoring" / "alpha_gate.prom"
    logs_root = repo_root / "logs" / "alpha_gate"
    existing_logs = set(logs_root.iterdir()) if logs_root.exists() else set()
    original_summary = (
        summary_path.read_text(encoding="utf-8") if summary_path.exists() else None
    )
    original_prom = (
        prom_path.read_text(encoding="utf-8") if prom_path.exists() else None
    )

    try:
        result = subprocess.run(
            [
                "bash",
                "scripts/run_alpha_gate.sh",
                "--skip-build",
                "--skip-health",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 123

        assert summary_path.exists()
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        tests_phase = summary_payload["phases"]["tests"]
        assert tests_phase["exit_code"] == 123
        assert tests_phase["success"] is False
    finally:
        if original_summary is not None:
            summary_path.write_text(original_summary, encoding="utf-8")
        elif summary_path.exists():
            summary_path.unlink()

        if original_prom is not None:
            prom_path.write_text(original_prom, encoding="utf-8")
        elif prom_path.exists():
            prom_path.unlink()

        if logs_root.exists():
            for entry in logs_root.iterdir():
                if entry not in existing_logs:
                    if entry.is_dir():
                        shutil.rmtree(entry, ignore_errors=True)
                    else:
                        try:
                            entry.unlink()
                        except FileNotFoundError:
                            pass
