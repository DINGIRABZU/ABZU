"""Compute quality scores for repository components.

The script runs ``ruff``, ``mypy`` and ``coverage`` for each provided
component path and maps the results to a 1–10 scale. Scores are persisted
in ``data/quality_history.json`` and surfaced in
``docs/component_status.md``. A short summary is also written to the
``CI_ARTIFACTS_DIR`` when set, otherwise to ``quality_summary.txt`` in
this directory.

Usage::

    python scripts/quality_score.py [component [component ...]]

Components default to the repository root when none are given.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = REPO_ROOT / "data" / "quality_history.json"
DOC_PATH = REPO_ROOT / "docs" / "component_status.md"
DEFAULT_ARTIFACT = REPO_ROOT / "quality_summary.txt"


def run(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Execute *cmd* capturing output."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))


def score_from_count(count: int) -> int:
    """Map a violation or error count to a 1–10 score."""
    return max(1, 10 - count)


def run_ruff(component: Path) -> tuple[int, str]:
    proc = run(["ruff", "--format", "json", str(component)])
    try:
        violations = len(json.loads(proc.stdout or "[]"))
    except json.JSONDecodeError:
        violations = 10
    return score_from_count(violations), proc.stdout


def run_mypy(component: Path) -> tuple[int, str]:
    proc = run(["mypy", "--hide-error-context", "--no-error-summary", str(component)])
    errors = sum(1 for line in proc.stdout.splitlines() if "error:" in line)
    return score_from_count(errors), proc.stdout


def run_coverage() -> dict:
    run(["coverage", "erase"])
    run(["coverage", "run", "-m", "pytest"])
    run(["coverage", "json", "-i", "-o", "coverage.json"])
    with open(REPO_ROOT / "coverage.json", "r", encoding="utf-8") as fh:
        return json.load(fh)["files"]


def coverage_score(component: Path, cov_data: dict) -> int:
    files = []
    for name, data in cov_data.items():
        path = Path(name)
        try:
            path.relative_to(component)
        except ValueError:
            continue
        files.append(data["summary"]["percent_covered"])
    if not files:
        return 1
    percent = sum(files) / len(files)
    return max(1, min(10, round(percent / 10)))


def update_history(timestamp: str, results: Dict[str, Dict[str, int]]) -> None:
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, "r", encoding="utf-8") as fh:
            history = json.load(fh)
    else:
        history = []
    history.append({"timestamp": timestamp, "results": results})
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)


def update_docs(timestamp: str, results: Dict[str, Dict[str, int]]) -> str:
    lines = [
        "# Component Quality Status",
        "",
        f"Generated on {timestamp}.",
        "",
        "| Component | Ruff | Mypy | Coverage | Overall |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, metrics in results.items():
        lines.append(
            f"| {name} | {metrics['ruff']} | {metrics['mypy']} | "
            f"{metrics['coverage']} | {metrics['overall']} |"
        )
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def write_artifact(summary: str) -> None:
    target_dir = Path(os.environ.get("CI_ARTIFACTS_DIR", REPO_ROOT))
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "quality_summary.txt"
    path.write_text(summary + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("components", nargs="*", default=["."], help="Paths to assess")
    args = parser.parse_args()

    components = [Path(c).resolve() for c in args.components]

    cov = run_coverage()

    results: Dict[str, Dict[str, int]] = {}
    for comp in components:
        ruff_s, _ = run_ruff(comp)
        mypy_s, _ = run_mypy(comp)
        cov_s = coverage_score(comp, cov)
        overall = round((ruff_s + mypy_s + cov_s) / 3)
        results[comp.name] = {
            "ruff": ruff_s,
            "mypy": mypy_s,
            "coverage": cov_s,
            "overall": overall,
        }

    ts = datetime.now(UTC).isoformat()
    update_history(ts, results)
    summary = update_docs(ts, results)
    write_artifact(summary)


if __name__ == "__main__":
    main()
