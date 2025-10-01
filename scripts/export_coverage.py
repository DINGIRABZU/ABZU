#!/usr/bin/env python3
"""Export coverage metrics to component_index.json,
generate HTML reports, and enforce thresholds."""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

from _stage_runtime import EnvironmentLimitedWarning, bootstrap

bootstrap(optional_modules=[])

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "component_index.json"
COVERAGE_JSON = REPO_ROOT / "coverage.json"
COVERAGE_MMD = REPO_ROOT / "coverage.mmd"
COVERAGE_SVG = REPO_ROOT / "coverage.svg"
PYTHON = sys.executable
ACTIVE_STATUSES = {"active"}
STAGE_A_COMPONENT_IDS = {
    "start_spiral_os",
    "spiral_os",
    "spiral_memory",
    "spiral_vector_db",
    "vector_memory",
}
THRESHOLD = 90.0
__version__ = "0.1.0"


def _run_coverage_command(args: list[str], description: str) -> bool:
    try:
        subprocess.run(args, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        warnings.warn(
            f"environment-limited: {description} failed ({exc})",
            EnvironmentLimitedWarning,
            stacklevel=2,
        )
        return False


def main() -> None:
    """Generate coverage reports, update metrics and enforce thresholds."""
    if not _run_coverage_command(
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
        "coverage JSON export",
    ):
        return
    if not _run_coverage_command(
        [
            PYTHON,
            "-m",
            "coverage",
            "html",
            "--fail-under=0",
        ],
        "coverage HTML export",
    ):
        return

    htmlcov_dir = REPO_ROOT / "htmlcov"
    if not htmlcov_dir.is_dir():
        warnings.warn(
            "environment-limited: coverage HTML directory htmlcov/ missing; "
            "skipping artifact export",
            EnvironmentLimitedWarning,
            stacklevel=2,
        )
        return

    if COVERAGE_SVG.exists():
        COVERAGE_SVG.unlink()

    if not _run_coverage_command(
        [
            PYTHON,
            "-m",
            "coverage_badge",
            "-o",
            str(COVERAGE_SVG),
        ],
        "coverage badge generation",
    ):
        return
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
    coverage_by_id: dict[str, float] = {}

    for component in index.get("components", []):
        raw_path = Path(component["path"])
        abs_path = (REPO_ROOT / raw_path).resolve()
        path_variants = {
            str(raw_path),
            str(raw_path).lstrip("./"),
            str(abs_path),
        }
        try:
            path_variants.add(str(abs_path.relative_to(REPO_ROOT)))
        except ValueError:
            pass

        files: list[float] = []
        for fname, data in coverage_data.items():
            fpath = Path(fname)
            try:
                rel = fpath.relative_to(REPO_ROOT)
            except ValueError:
                rel = fpath

            rel_str = str(rel)
            fpath_str = str(fpath)

            if abs_path.is_dir():
                if not any(
                    rel_str == variant.rstrip("/")
                    or rel_str.startswith(variant.rstrip("/") + "/")
                    for variant in path_variants
                ):
                    continue
            else:
                if not any(
                    rel_str == variant.rstrip("/") or fpath_str == variant.rstrip("/")
                    for variant in path_variants
                ):
                    continue

            files.append(data["summary"]["percent_covered"])
        coverage = round(sum(files) / len(files), 2) if files else 0.0
        coverage_by_id[component.get("id", "unknown")] = coverage
        metrics = component.setdefault("metrics", {})
        metrics["coverage"] = coverage

    for component in index.get("components", []):
        comp_id = component.get("id")
        if comp_id not in STAGE_A_COMPONENT_IDS:
            continue
        coverage = coverage_by_id.get(comp_id, 0.0)
        if component.get("status") in ACTIVE_STATUSES and coverage < THRESHOLD:
            failures.append((comp_id, coverage))

    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    if failures:
        for comp, cov in failures:
            print(f"{comp} coverage {cov}% below {THRESHOLD}%", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
