"""Aggregate Stage A/B readiness evidence into a Stage C bundle.

This helper consolidates the latest readiness summaries from Stage A and
Stage B together with supporting telemetry references. The resulting bundle
is written to the Stage C run directory supplied on the command line so the
Stage C readiness sync endpoint can surface a complete snapshot.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STAGE_A_ROOT = Path("logs") / "stage_a"
STAGE_B_ROOT = Path("logs") / "stage_b"
BUNDLE_FILENAME = "readiness_bundle.json"
SUMMARY_FILENAME = "summary.json"


def _latest_summary(stage_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    if not stage_root.exists():
        return None, None
    summary_files = sorted(stage_root.glob("*/summary.json"))
    if not summary_files:
        return None, None
    latest = max(summary_files)
    data = json.loads(latest.read_text(encoding="utf-8"))
    return latest, data


def _collect_supporting_artifacts(summary: dict[str, Any] | None) -> list[str]:
    if not summary:
        return []

    log_dir_value = summary.get("log_dir")
    if not log_dir_value:
        return []

    log_dir = Path(log_dir_value)
    if not log_dir.exists():
        return []

    artifacts: list[str] = []
    for candidate in sorted(log_dir.iterdir()):
        if candidate.name == "summary.json" or candidate.is_dir():
            continue
        artifacts.append(str(candidate))
    return artifacts


def _extract_risk_notes(summary: dict[str, Any] | None) -> list[str]:
    if not summary:
        return ["readiness summary missing"]

    notes: list[str] = []
    status = summary.get("status")
    if status and status != "success":
        error = summary.get("error")
        if error:
            notes.append(str(error))

        stderr_tail = summary.get("stderr_tail")
        if isinstance(stderr_tail, Iterable) and not isinstance(stderr_tail, (str, bytes)):
            notes.extend(str(line) for line in stderr_tail if str(line).strip())
        elif isinstance(stderr_tail, (str, bytes)) and stderr_tail:
            notes.append(str(stderr_tail))

    warnings = summary.get("warnings") if summary else None
    if isinstance(warnings, Iterable) and not isinstance(warnings, (str, bytes)):
        notes.extend(str(item) for item in warnings if str(item).strip())
    elif isinstance(warnings, (str, bytes)) and warnings:
        notes.append(str(warnings))

    return notes


def _build_stage_snapshot(
    stage_label: str,
    summary_path: Path | None,
    summary: dict[str, Any] | None,
) -> dict[str, Any]:
    artifacts = _collect_supporting_artifacts(summary)
    snapshot: dict[str, Any] = {
        "label": stage_label,
        "summary_path": str(summary_path) if summary_path else None,
        "summary": summary,
        "artifacts": artifacts,
        "risk_notes": _extract_risk_notes(summary),
    }
    return snapshot


def _merge_stage_data(stage_a: dict[str, Any], stage_b: dict[str, Any]) -> dict[str, Any]:
    def _latest(attr: str, data: dict[str, Any]) -> Any:
        summary = data.get("summary") or {}
        return summary.get(attr)

    merged = {
        "latest_runs": {
            "stage_a": _latest("run_id", stage_a),
            "stage_b": _latest("run_id", stage_b),
        },
        "completed_at": {
            "stage_a": _latest("completed_at", stage_a),
            "stage_b": _latest("completed_at", stage_b),
        },
        "status_flags": {
            "stage_a": _latest("status", stage_a) or "missing",
            "stage_b": _latest("status", stage_b) or "missing",
        },
        "risk_notes": {
            "stage_a": stage_a.get("risk_notes", []),
            "stage_b": stage_b.get("risk_notes", []),
        },
    }

    stages = merged["status_flags"].values()
    if all(status == "success" for status in stages):
        merged["overall_status"] = "ready"
    else:
        merged["overall_status"] = "requires_attention"
    return merged


def aggregate(stage_c_log_dir: Path) -> tuple[Path, dict[str, Any]]:
    stage_c_log_dir.mkdir(parents=True, exist_ok=True)

    stage_a_path, stage_a_summary = _latest_summary(STAGE_A_ROOT)
    stage_b_path, stage_b_summary = _latest_summary(STAGE_B_ROOT)

    stage_a_snapshot = _build_stage_snapshot("stage_a", stage_a_path, stage_a_summary)
    stage_b_snapshot = _build_stage_snapshot("stage_b", stage_b_path, stage_b_summary)

    merged = _merge_stage_data(stage_a_snapshot, stage_b_snapshot)
    missing = [
        label
        for label, snapshot in (
            ("stage_a", stage_a_snapshot),
            ("stage_b", stage_b_snapshot),
        )
        if not snapshot.get("summary")
    ]

    bundle = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "stage_a": stage_a_snapshot,
        "stage_b": stage_b_snapshot,
        "merged": merged,
        "missing": missing,
    }

    bundle_path = stage_c_log_dir / BUNDLE_FILENAME
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    summary_payload = {
        "status": "success" if not missing else "error",
        "generated_at": bundle["generated_at"],
        "bundle_path": str(bundle_path),
        "stage_a": stage_a_snapshot,
        "stage_b": stage_b_snapshot,
        "merged": merged,
        "missing": missing,
    }

    summary_path = stage_c_log_dir / SUMMARY_FILENAME
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    return bundle_path, summary_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage_c_log_dir",
        help="Path to the Stage C run directory where the bundle should be written.",
    )
    args = parser.parse_args()

    stage_c_log_dir = Path(args.stage_c_log_dir)
    bundle_path, summary_payload = aggregate(stage_c_log_dir)
    print(json.dumps(summary_payload, indent=2))

    return 0 if summary_payload["status"] == "success" else 1


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
