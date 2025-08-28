"""Prioritized pytest runner for RAZAR.

The runner executes test modules in priority order as defined in
``tests/priority_map.yaml``. Results from each module append to
``logs/pytest_priority.log`` and the path of the last failing test is stored in
``logs/pytest_state.json``. Supplying ``--resume`` resumes execution from that
failing test after fixes.
"""

from __future__ import annotations

import argparse
import contextlib
import json
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List

import pytest
import yaml

PRIORITY_LEVELS = ["P1", "P2", "P3", "P4", "P5"]


def load_priority_map(map_path: Path) -> Dict[str, List[str]]:
    """Return mapping of priority tiers to test file paths."""
    data = yaml.safe_load(map_path.read_text("utf-8")) or {}
    mapping: Dict[str, List[str]] = {}
    for tier in PRIORITY_LEVELS:
        tests = data.get(tier)
        if isinstance(tests, list):
            mapping[tier] = [str(t) for t in tests]
    return mapping


def run_tests(
    priorities: Iterable[str] | None,
    resume: bool,
    map_path: Path,
    log_path: Path,
    state_path: Path,
) -> int:
    """Run pytest on tests grouped by ``priorities``."""

    priority_map = load_priority_map(map_path)
    selected = [p for p in PRIORITY_LEVELS if priorities is None or p in priorities]

    # Flatten tests preserving order
    tests: List[str] = []
    for tier in selected:
        tests.extend(priority_map.get(tier, []))

    start_index = 0
    if resume and state_path.exists():
        state = json.loads(state_path.read_text("utf-8"))
        last = state.get("last_failed")
        if last in tests:
            start_index = tests.index(last)
    else:
        if state_path.exists():
            state_path.unlink()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    for test in tests[start_index:]:
        stream = StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            exit_code = pytest.main([test])
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"=== {test} ===\n{stream.getvalue()}\n")
        if exit_code != 0:
            state_path.write_text(json.dumps({"last_failed": test}), "utf-8")
            return exit_code

    if state_path.exists():
        state_path.unlink()
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run prioritized pytest tiers")
    parser.add_argument(
        "--priority",
        choices=PRIORITY_LEVELS,
        nargs="*",
        help="Run only the specified priority tiers",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last failing test stored in logs/pytest_state.json",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(__file__).resolve().parents[2]
    map_path = repo_root / "tests" / "priority_map.yaml"
    log_path = repo_root / "logs" / "pytest_priority.log"
    state_path = repo_root / "logs" / "pytest_state.json"
    return run_tests(args.priority, args.resume, map_path, log_path, state_path)


if __name__ == "__main__":
    raise SystemExit(main())
