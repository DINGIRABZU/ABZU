#!/usr/bin/env python3
"""Run pytest and record failing cases for documentation."""
from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path

REPORT_PATH = Path("logs/test_report.txt")
DOC_PATH = Path("docs/testing/failure_inventory.md")


def main() -> None:
    cmd = ["pytest", "-vv"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(result.stdout + "\n" + result.stderr)

    output_lines = (result.stdout + "\n" + result.stderr).splitlines()
    failures = []
    for line in output_lines:
        stripped = line.strip()
        if stripped.startswith("FAILED") or stripped.startswith("ERROR"):
            failures.append(stripped)

    today = dt.datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Failure Inventory",
        "",
        f"Test run: `pytest -vv` on {today}.",
        "",
        "## Failures",
    ]
    if failures:
        lines.extend(f"- {f}" for f in failures)
    else:
        lines.append("- No failures detected.")
    lines.extend(
        [
            "",
            "See [logs/test_report.txt](../../logs/test_report.txt) for full pytest output.",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(lines))

    # Do not block commits even if tests fail
    return


if __name__ == "__main__":
    main()
