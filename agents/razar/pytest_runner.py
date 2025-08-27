"""Run prioritized pytest suites for RAZAR.

The runner reads :mod:`tests/priority_map.yaml` to determine which test files
belong to priority tiers ``P1`` through ``P5``.  Command line flags allow
executing a subset of tiers and resuming from the last failing session using
``pytest``'s ``--last-failed`` mechanism.  Output is written to
``logs/pytest_priority.log`` for downstream analysis.
"""

from __future__ import annotations

import argparse
import contextlib
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List

import pytest
import yaml

PRIORITY_LEVELS = ("P1", "P2", "P3", "P4", "P5")


def load_priority_map(map_path: Path) -> Dict[str, List[str]]:
    """Load the priority mapping from ``map_path``.

    The YAML file should map priority keys (``P1``–``P5``) to lists of test
    paths.  Unknown keys are ignored.
    """

    if not map_path.exists():
        return {}

    data = yaml.safe_load(map_path.read_text("utf-8")) or {}
    mapping: Dict[str, List[str]] = {}
    for key, value in data.items():
        key_upper = str(key).upper()
        if key_upper in PRIORITY_LEVELS and isinstance(value, list):
            mapping[key_upper] = [str(v) for v in value]
    return mapping


def run_pytest(
    priorities: Iterable[str] | None,
    resume: bool,
    log_path: Path,
    map_path: Path,
) -> int:
    """Execute pytest for the selected priority tiers."""

    priority_map = load_priority_map(map_path)
    selected = [p.upper() for p in (priorities or PRIORITY_LEVELS)]
    tests: List[str] = []
    for tier in selected:
        tests.extend(priority_map.get(tier, []))

    if not tests:
        # Avoid running the entire suite if nothing matches
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("No tests matched given priorities\n", "utf-8")
        return 0

    args: List[str] = tests
    if resume:
        # ``--failed-first`` runs previously failing tests before the rest
        args.extend(["--last-failed", "--failed-first"])

    log_path.parent.mkdir(parents=True, exist_ok=True)
    stream = StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        exit_code = pytest.main(args)

    log_path.write_text(stream.getvalue(), "utf-8")
    return exit_code


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description="Run prioritized pytest suites")
    parser.add_argument(
        "--priority",
        choices=list(PRIORITY_LEVELS),
        nargs="*",
        help="Run only the specified priority levels",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last failing tests using pytest's --last-failed option",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(__file__).resolve().parents[2]
    log_path = repo_root / "logs" / "pytest_priority.log"
    map_path = repo_root / "tests" / "priority_map.yaml"
    return run_pytest(args.priority, args.resume, log_path, map_path)


if __name__ == "__main__":
    raise SystemExit(main())

