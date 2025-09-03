#!/usr/bin/env python3
"""Run milestone checks for operator copresence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

__version__ = "0.1.0"


def run_step(
    name: str, cmd: list[str], *, env: dict[str, str] | None = None
) -> dict[str, object]:
    """Execute *cmd* and capture output and status."""
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    output = proc.stdout
    return {"returncode": proc.returncode, "output": output}


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(repo_root / "src"))

    steps: list[tuple[str, list[str], dict[str, str] | None]] = [
        ("pytest", ["pytest", "--cov"], None),
        (
            "update_error_index",
            [sys.executable, str(repo_root / "scripts" / "update_error_index.py")],
            None,
        ),
        (
            "validate_ignition",
            [sys.executable, str(repo_root / "scripts" / "validate_ignition.py")],
            None,
        ),
        (
            "operator_console_smoke",
            [sys.executable, "-m", "cli.console_interface", "--help"],
            env,
        ),
    ]

    results: dict[str, dict[str, object]] = {}
    for name, cmd, cmd_env in steps:
        results[name] = run_step(name, cmd, env=cmd_env)

    failures = [name for name, res in results.items() if res["returncode"] != 0]
    results["triage"] = failures

    logs_dir = repo_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    out_path = logs_dir / "milestone_copresence_beta.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
