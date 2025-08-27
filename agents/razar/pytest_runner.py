"""Run pytest suites by priority tiers for RAZAR.

This runner leverages the :mod:`pytest` test framework together with the
``pytest-order`` plugin to categorise tests into five priority levels: ``P1``
through ``P5``. Tests should mark their priority with ``@pytest.mark.p1`` ...
``@pytest.mark.p5``. The runner exposes command line flags to execute specific
priority levels or resume from the last failing test session. All output is
written to ``logs/pytest_priority.log`` for consumption by RAZAR's decision
engine.
"""

from __future__ import annotations

import argparse
import contextlib
from io import StringIO
import os
from typing import Iterable, List

import pytest
import pytest_order  # ensure plugin is loaded

# Mapping of priority marker names to their execution order
PRIORITY_ORDER = {
    "p1": 1,
    "p2": 2,
    "p3": 3,
    "p4": 4,
    "p5": 5,
}


class PriorityPlugin:
    """Translate priority markers into ``pytest-order`` indices."""

    def pytest_configure(self, config: pytest.Config) -> None:  # pragma: no cover - pytest hook
        for name in PRIORITY_ORDER:
            config.addinivalue_line("markers", f"{name}: priority level {name.upper()}")

    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: List[pytest.Item]
    ) -> None:  # pragma: no cover - pytest hook
        for item in items:
            for marker, order in PRIORITY_ORDER.items():
                if marker in item.keywords:
                    item.add_marker(pytest.mark.order(order))
                    break


def run_pytest(priority: Iterable[str] | None, resume: bool, log_path: str) -> int:
    """Execute pytest with the given options and write output to ``log_path``."""

    args: List[str] = []
    if priority:
        expr = " or ".join(p.lower() for p in priority)
        args.extend(["-m", expr])
    if resume:
        # ``--failed-first`` ensures any remaining tests run after the failures
        args.extend(["--last-failed", "--failed-first"])

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    stream = StringIO()
    plugin = PriorityPlugin()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        exit_code = pytest.main(args, plugins=[plugin])

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(stream.getvalue())

    return exit_code


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description="Run prioritized pytest suites")
    parser.add_argument(
        "--priority",
        choices=["P1", "P2", "P3", "P4", "P5"],
        nargs="*",
        help="Run only the specified priority levels.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last failing tests using pytest's --last-failed option.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    log_path = os.path.join("logs", "pytest_priority.log")
    return run_pytest(args.priority, args.resume, log_path)


if __name__ == "__main__":
    raise SystemExit(main())
