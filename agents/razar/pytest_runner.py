"""Run prioritized pytest suites for RAZAR.

The runner reads :mod:`tests/priority_map.yaml` to determine which test files
belong to priority tiers ``P1`` through ``P5``.  Tiers are executed in order so
critical smoke tests can fail fast.  The location of the last failing test is
persisted in ``logs/pytest_last_failed.json`` so subsequent invocations with the
``--resume`` flag continue from the failing tier using pytest's ``--last-failed``
support.  Output from each tier is appended to ``logs/pytest_priority.log`` for
downstream analysis.
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

PRIORITY_LEVELS = ("P1", "P2", "P3", "P4", "P5")
STATE_FILE = "pytest_last_failed.json"


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


def _load_state(state_path: Path) -> Dict[str, str]:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text("utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(state_path: Path, tier: str, nodeid: str) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"tier": tier, "nodeid": nodeid}), "utf-8")


def _clear_state(state_path: Path) -> None:
    if state_path.exists():
        state_path.unlink()


def _last_failed(repo_root: Path) -> str:
    cache = repo_root / ".pytest_cache" / "v" / "cache" / "lastfailed"
    if cache.exists():
        try:
            data = json.loads(cache.read_text("utf-8"))
            if data:
                return next(iter(data))
        except json.JSONDecodeError:
            return ""
    return ""


def run_pytest(
    priorities: Iterable[str] | None,
    resume: bool,
    log_path: Path,
    map_path: Path,
    state_path: Path,
) -> int:
    """Execute pytest for the selected priority tiers."""

    priority_map = load_priority_map(map_path)
    selected = [p.upper() for p in (priorities or PRIORITY_LEVELS)]

    state = _load_state(state_path) if resume else {}
    start_tier = state.get("tier")
    repo_root = log_path.parent.parent

    try:
        start_index = selected.index(start_tier) if start_tier else 0
    except ValueError:
        start_index = 0

    exit_code = 0
    log_path.parent.mkdir(parents=True, exist_ok=True)
    for idx, tier in enumerate(selected):
        if idx < start_index:
            continue
        tests = priority_map.get(tier, [])
        if not tests:
            continue
        args: List[str] = ["-p", "pytest_order", *tests]
        if resume and idx == start_index and state.get("nodeid"):
            args.extend(["--last-failed", "--failed-first"])

        stream = StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            exit_code = pytest.main(args)

        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"=== {tier} ===\n")
            fh.write(stream.getvalue())

        if exit_code != 0:
            failing = _last_failed(repo_root)
            _save_state(state_path, tier, failing)
            break

    if exit_code == 0:
        _clear_state(state_path)

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
    state_path = log_path.parent / STATE_FILE
    return run_pytest(args.priority, args.resume, log_path, map_path, state_path)


if __name__ == "__main__":
    raise SystemExit(main())
