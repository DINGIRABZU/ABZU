#!/usr/bin/env python3
"""Run pytest and record failing cases for documentation."""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

REPORT_PATH = Path("logs/test_report.txt")
DOC_PATH = Path("docs/testing/failure_inventory.md")


def main() -> None:
    """Run pytest and append failing tests to the failure inventory."""
    cmd = ["pytest", "-vv", *sys.argv[1:]]
    result = subprocess.run(cmd, capture_output=True, text=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(result.stdout + "\n" + result.stderr)

    output_lines = (result.stdout + "\n" + result.stderr).splitlines()
    failures: list[str] = []
    for line in output_lines:
        stripped = line.strip()
        if stripped.startswith("FAILED") or stripped.startswith("ERROR"):
            failures.append(stripped)

    today = dt.datetime.now().strftime("%Y-%m-%d")

    if DOC_PATH.exists():
        doc_lines = DOC_PATH.read_text().splitlines()
    else:
        doc_lines = [
            "# Failure Inventory",
            "",
            "Failures from `pytest` runs are appended via "
            "[`scripts/capture_failing_tests.py`](../../scripts/capture_failing_tests.py).",
            "",
            "## Failures",
        ]

    if failures:
        new_lines = [f"- {today}: {f}" for f in failures]
    else:
        new_lines = [f"- {today}: No failures detected."]

    existing_entries = {line.strip() for line in doc_lines if line.startswith("-")}
    to_append = [line for line in new_lines if line.strip() not in existing_entries]
    if not to_append:
        return
    if doc_lines and doc_lines[-1] != "":
        doc_lines.append("")
    doc_lines.extend(to_append)
    DOC_PATH.write_text("\n".join(doc_lines) + "\n")

    # Do not block commits even if tests fail
    return


if __name__ == "__main__":
    main()
