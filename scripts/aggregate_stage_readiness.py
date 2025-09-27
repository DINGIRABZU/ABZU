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
import logging
from pathlib import Path
import shutil
import re
from typing import Any, Iterable, Mapping


STAGE_A_ROOT = Path("logs") / "stage_a"
STAGE_B_ROOT = Path("logs") / "stage_b"
BUNDLE_FILENAME = "readiness_bundle.json"
SUMMARY_FILENAME = "summary.json"
STAGE_A_EXPECTED_SLUGS = ("A1", "A2", "A3")


LOGGER = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_path(value: Any) -> Path | None:
    if not value:
        return None
    try:
        candidate = Path(str(value))
    except TypeError:
        return None
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def _copy_into_stage_c(source: Path, stage_c_dir: Path, base_name: str) -> Path:
    suffix = "".join(source.suffixes)
    destination_name = base_name + suffix if suffix else base_name
    destination = stage_c_dir / destination_name
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    except FileNotFoundError:
        LOGGER.warning("stage readiness copy missing source: %s", source)
    except OSError as exc:
        LOGGER.warning(
            "stage readiness failed to copy %s -> %s: %s", source, destination, exc
        )
    return destination


def _materialize_entry_files(
    entry: Mapping[str, Any] | None,
    stage_c_dir: Path,
    stage_label: str,
    slug: str | None = None,
) -> None:
    if not isinstance(entry, dict):
        return

    target_key = f"{stage_label}"
    if slug:
        target_key = f"{target_key}-{slug.lower()}"

    summary_path_value = entry.get("summary_path") if isinstance(entry, dict) else None
    if summary_path_value:
        source_summary = _resolve_path(summary_path_value)
        if source_summary:
            entry["source_summary_path"] = str(source_summary)
            copied_summary = _copy_into_stage_c(
                source_summary, stage_c_dir, f"{target_key}-summary"
            )
            entry["summary_path"] = str(copied_summary)

    artifacts_value = entry.get("artifacts")
    if isinstance(artifacts_value, list):
        copied_artifacts: list[str] = []
        source_artifacts: list[str] = []
        for index, artifact in enumerate(artifacts_value, start=1):
            if not artifact:
                continue
            source_artifact = _resolve_path(artifact)
            if source_artifact:
                source_artifacts.append(str(source_artifact))
                copied_artifact = _copy_into_stage_c(
                    source_artifact, stage_c_dir, f"{target_key}-artifact{index}"
                )
                copied_artifacts.append(str(copied_artifact))
            else:
                source_artifacts.append(str(artifact))
                copied_artifacts.append(str(artifact))
        entry["source_artifacts"] = source_artifacts
        entry["artifacts"] = copied_artifacts


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    candidate = value
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _slug_from_text(text: str) -> str | None:
    match = re.search(r"stage[_-]?(a\d)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b(a\d)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _extract_slug(summary: Mapping[str, Any] | None, summary_path: Path) -> str:
    if summary is not None:
        for key in ("slug", "stage", "run_id"):
            value = summary.get(key)
            if isinstance(value, str):
                slug = _slug_from_text(value)
                if slug:
                    return slug
    slug = _slug_from_text(summary_path.parent.name)
    if slug:
        return slug
    return "UNKNOWN"


def _latest_by_slug(stage_root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    results: dict[str, tuple[Path, dict[str, Any]]] = {}
    if not stage_root.exists():
        return results
    for summary_path in sorted(stage_root.glob("*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        slug = _extract_slug(summary, summary_path)
        existing = results.get(slug)
        if existing:
            _, existing_summary = existing
            existing_completed = _parse_datetime(existing_summary.get("completed_at"))
            current_completed = _parse_datetime(summary.get("completed_at"))
            if existing_completed and current_completed:
                if current_completed <= existing_completed:
                    continue
            elif existing_completed and not current_completed:
                continue
            elif not existing_completed and not current_completed:
                if str(summary_path) <= str(existing[0]):
                    continue
        results[slug] = (summary_path, summary)
    return results


def _latest_summary(stage_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    if not stage_root.exists():
        return None, None
    summary_files = sorted(stage_root.glob("*/summary.json"))
    if not summary_files:
        return None, None
    latest = max(summary_files)
    data = json.loads(latest.read_text(encoding="utf-8"))
    return latest, data


def _collect_supporting_artifacts(summary: Mapping[str, Any] | None) -> list[str]:
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


def _extract_risk_notes(summary: Mapping[str, Any] | None) -> list[str]:
    if not summary:
        return ["readiness summary missing"]

    notes: list[str] = []
    status = summary.get("status")
    if status and status != "success":
        error = summary.get("error")
        if error:
            notes.append(str(error))

        stderr_tail = summary.get("stderr_tail")
        if isinstance(stderr_tail, Iterable) and not isinstance(
            stderr_tail, (str, bytes)
        ):
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
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    artifacts = _collect_supporting_artifacts(summary)
    status = "missing"
    latest_run: str | None = None
    completed_at: str | None = None
    if summary:
        status = str(summary.get("status") or "missing")
        latest_run = (
            summary.get("run_id") if isinstance(summary.get("run_id"), str) else None
        )
        completed_at = (
            summary.get("completed_at")
            if isinstance(summary.get("completed_at"), str)
            else None
        )

    snapshot: dict[str, Any] = {
        "label": stage_label,
        "summary_path": str(summary_path) if summary_path else None,
        "summary": summary,
        "artifacts": artifacts,
        "risk_notes": _extract_risk_notes(summary),
        "status": status,
        "latest_runs": latest_run,
        "completed_at": completed_at,
    }
    return snapshot


def _build_stage_a_snapshot() -> tuple[dict[str, Any], list[str]]:
    latest = _latest_by_slug(STAGE_A_ROOT)
    slugs = sorted({*latest.keys(), *STAGE_A_EXPECTED_SLUGS})
    slug_entries: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    aggregated_risk_notes: list[str] = []
    latest_runs: dict[str, str | None] = {}
    completed_at: dict[str, str | None] = {}
    for slug in slugs:
        summary_path: Path | None = None
        summary: Mapping[str, Any] | None = None
        if slug in latest:
            summary_path, summary = latest[slug]
        artifacts = _collect_supporting_artifacts(summary)
        risk_notes = _extract_risk_notes(summary)
        status = "missing"
        run_id: str | None = None
        completed: str | None = None
        if summary:
            run_id = (
                summary.get("run_id")
                if isinstance(summary.get("run_id"), str)
                else None
            )
            completed = (
                summary.get("completed_at")
                if isinstance(summary.get("completed_at"), str)
                else None
            )
            status = str(summary.get("status") or "missing")
        else:
            missing.append(f"stage_a:{slug.lower()}")
        aggregated_risk_notes.extend(risk_notes)
        latest_runs[slug] = run_id
        completed_at[slug] = completed
        slug_entries[slug] = {
            "slug": slug,
            "summary_path": str(summary_path) if summary_path else None,
            "summary": summary,
            "artifacts": artifacts,
            "risk_notes": risk_notes,
            "status": status,
        }

    if not slug_entries:
        overall_status = "missing"
    else:
        statuses = [entry["status"] for entry in slug_entries.values()]
        if all(status == "missing" for status in statuses):
            overall_status = "missing"
        elif all(status == "success" for status in statuses):
            overall_status = "success"
        else:
            overall_status = "requires_attention"

    snapshot = {
        "label": "stage_a",
        "status": overall_status,
        "risk_notes": aggregated_risk_notes,
        "slugs": slug_entries,
        "latest_runs": latest_runs,
        "completed_at": completed_at,
    }
    if overall_status == "missing" and not missing:
        missing.append("stage_a")
    return snapshot, missing


def _merge_stage_data(
    stage_a: dict[str, Any], stage_b: dict[str, Any]
) -> dict[str, Any]:
    stage_a_status = str(stage_a.get("status") or "missing")
    stage_b_status = str(stage_b.get("status") or "missing")

    stage_a_slugs = {
        slug: {
            "status": entry.get("status", "missing"),
            "risk_notes": entry.get("risk_notes", []),
            "run_id": (
                entry.get("summary", {}).get("run_id")
                if isinstance(entry.get("summary"), Mapping)
                else None
            ),
            "completed_at": (
                entry.get("summary", {}).get("completed_at")
                if isinstance(entry.get("summary"), Mapping)
                else None
            ),
        }
        for slug, entry in stage_a.get("slugs", {}).items()
        if isinstance(entry, Mapping)
    }

    merged = {
        "latest_runs": {
            "stage_a": stage_a.get("latest_runs"),
            "stage_b": stage_b.get("latest_runs"),
        },
        "completed_at": {
            "stage_a": stage_a.get("completed_at"),
            "stage_b": stage_b.get("completed_at"),
        },
        "status_flags": {
            "stage_a": stage_a_status,
            "stage_b": stage_b_status,
        },
        "risk_notes": {
            "stage_a": stage_a.get("risk_notes", []),
            "stage_b": stage_b.get("risk_notes", []),
        },
        "stage_a_slugs": stage_a_slugs,
    }

    stages = merged["status_flags"].values()
    if all(status == "success" for status in stages):
        merged["overall_status"] = "ready"
    else:
        merged["overall_status"] = "requires_attention"
    return merged


def aggregate(stage_c_log_dir: Path) -> tuple[Path, dict[str, Any]]:
    stage_c_log_dir.mkdir(parents=True, exist_ok=True)

    stage_a_snapshot, stage_a_missing = _build_stage_a_snapshot()
    stage_b_path, stage_b_summary = _latest_summary(STAGE_B_ROOT)

    stage_b_snapshot = _build_stage_snapshot("stage_b", stage_b_path, stage_b_summary)

    if isinstance(stage_b_snapshot, dict):
        _materialize_entry_files(stage_b_snapshot, stage_c_log_dir, "stage_b")

    stage_a_slugs = stage_a_snapshot.get("slugs")
    if isinstance(stage_a_slugs, Mapping):
        for slug, slug_entry in stage_a_slugs.items():
            _materialize_entry_files(slug_entry, stage_c_log_dir, "stage_a", str(slug))
    else:
        _materialize_entry_files(stage_a_snapshot, stage_c_log_dir, "stage_a")

    merged = _merge_stage_data(stage_a_snapshot, stage_b_snapshot)
    missing = list(stage_a_missing)
    if not stage_b_snapshot.get("summary"):
        missing.append("stage_b")

    bundle = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "stage_a": stage_a_snapshot,
        "stage_b": stage_b_snapshot,
        "merged": merged,
        "missing": missing,
    }

    bundle_path = stage_c_log_dir / BUNDLE_FILENAME
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    status = (
        "success" if merged["overall_status"] == "ready" and not missing else "error"
    )
    error: str | None = None
    if missing:
        error = "missing readiness summaries: " + ", ".join(missing)
    elif merged["overall_status"] != "ready":
        attention_parts: list[str] = []
        if merged["status_flags"].get("stage_a") != "success":
            attention_parts.append("stage_a")
        if merged["status_flags"].get("stage_b") != "success":
            attention_parts.append("stage_b")
        if attention_parts:
            error = "readiness requires_attention: " + ", ".join(attention_parts)

    summary_payload = {
        "status": status,
        "generated_at": bundle["generated_at"],
        "bundle_path": str(bundle_path),
        "stage_a": stage_a_snapshot,
        "stage_b": stage_b_snapshot,
        "merged": merged,
        "missing": missing,
    }
    if error:
        summary_payload["error"] = error

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
