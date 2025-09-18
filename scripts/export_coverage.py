#!/usr/bin/env python3
"""Export coverage metrics to component_index.json,
generate HTML reports, and enforce thresholds."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "component_index.json"
COVERAGE_JSON = REPO_ROOT / "coverage.json"
COVERAGE_MMD = REPO_ROOT / "coverage.mmd"
PYTHON = sys.executable
ACTIVE_STATUSES = {"active"}
THRESHOLD = 90.0
__version__ = "0.1.0"


def main() -> None:
    """Generate coverage reports, update metrics and enforce thresholds."""
    subprocess.run(
        [
            PYTHON,
            "-m",
            "coverage",
            "json",
            "-i",
            "--fail-under=0",
            "-o",
            str(COVERAGE_JSON),
        ],
        check=True,
    )
    with COVERAGE_JSON.open("r", encoding="utf-8") as fh:
        coverage_payload = json.load(fh)

    totals = coverage_payload.get("totals", {})
    covered_statements = int(totals.get("covered_lines", 0))
    total_statements = int(totals.get("num_statements", 0))
    missed_statements = max(total_statements - covered_statements, 0)

    COVERAGE_MMD.write_text(
        (
            "pie showData\n"
            f'    "Covered" : {covered_statements}\n'
            f'    "Missed" : {missed_statements}\n'
        ),
        encoding="utf-8",
    )

    coverage_data = coverage_payload["files"]
    with INDEX_PATH.open("r", encoding="utf-8") as fh:
        index = json.load(fh)

    failures: list[tuple[str, float]] = []

    for component in index.get("components", []):
        path = REPO_ROOT / component["path"]
        files: list[float] = []
        for fname, data in coverage_data.items():
            fpath = Path(fname)
            try:
                rel = fpath.relative_to(REPO_ROOT)
            except ValueError:
                rel = fpath
            if path.is_dir():
                try:
                    rel.relative_to(path)
                except ValueError:
                    continue
            else:
                if rel != path:
                    continue
            files.append(data["summary"]["percent_covered"])
        coverage = round(sum(files) / len(files), 2) if files else 0.0
        metrics = component.setdefault("metrics", {})
        metrics["coverage"] = coverage
        if component.get("status") in ACTIVE_STATUSES and coverage < THRESHOLD:
            failures.append((component.get("id", "unknown"), coverage))

    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    if failures:
        for comp, cov in failures:
            print(f"{comp} coverage {cov}% below {THRESHOLD}%", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
