"""Coordinate Stage B rehearsal checks and persist monitoring artifacts."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from scripts import health_check_connectors

__version__ = "0.1.0"

LOGGER = logging.getLogger("stage_b.rehearsal_scheduler")

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = REPO_ROOT / "monitoring" / "stage_b"
ROTATION_LOG = REPO_ROOT / "logs" / "stage_b_rotation_drills.jsonl"

SUMMARY_FILENAME = "rehearsal_summary.json"
PROMETHEUS_FILENAME = "rehearsal_status.prom"
HEALTH_FILENAME = "health_checks.json"
STAGE_B_FILENAME = "stage_b_smoke.json"
ROTATION_FILENAME = "rotation_drills.json"

EXPECTED_ROTATION_CONNECTORS: tuple[str, ...] = ("operator_api", "operator_upload")


def _iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:  # pragma: no cover - defensive, should not trigger in repo
        return str(path)


def _load_rotation_entries(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                entries.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    return entries


def extract_new_rotation_entries(
    previous: Iterable[Mapping[str, Any]],
    current: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Return Stage B rotation entries appended between snapshots."""

    seen = {json.dumps(entry, sort_keys=True) for entry in previous}
    new_entries: List[Dict[str, Any]] = []
    for entry in current:
        try:
            key = json.dumps(entry, sort_keys=True)
        except TypeError:
            continue
        if key in seen:
            continue
        new_entries.append(dict(entry))
    return new_entries


def summarise_health_results(results: Dict[str, bool]) -> Dict[str, Any]:
    """Normalise connector and remote agent probe outcomes."""

    details: List[Dict[str, Any]] = []
    for name in sorted(results):
        details.append(
            {
                "name": name,
                "ok": bool(results[name]),
                "kind": (
                    "connector"
                    if name in health_check_connectors.CONNECTORS
                    else "remote"
                ),
            }
        )

    ok = bool(details) and all(item["ok"] for item in details)
    return {"ok": ok, "results": details, "raw": results}


def _bool_to_int(value: bool | None) -> int:
    return 1 if value else 0


def render_prometheus_metrics(summary: Mapping[str, Any]) -> str:
    """Render Prometheus gauges describing the rehearsal run."""

    lines: List[str] = []

    run_ok = bool(summary.get("overall_ok"))
    lines.extend(
        [
            (
                "# HELP stage_b_rehearsal_run_status "
                "Stage B rehearsal overall success (1=ok)"
            ),
            "# TYPE stage_b_rehearsal_run_status gauge",
            f"stage_b_rehearsal_run_status {_bool_to_int(run_ok)}",
        ]
    )

    health = summary.get("health_checks", {})
    health_ok = health.get("ok")
    lines.extend(
        [
            (
                "# HELP stage_b_rehearsal_health_status "
                "Connector and agent health results (1=ok)"
            ),
            "# TYPE stage_b_rehearsal_health_status gauge",
            f"stage_b_rehearsal_health_status {_bool_to_int(health_ok)}",
        ]
    )
    for item in health.get("results", []):
        name = item.get("name", "unknown")
        kind = item.get("kind", "connector")
        value = _bool_to_int(item.get("ok"))
        lines.append(
            (
                'stage_b_rehearsal_health_check{target="'
                f'{name}",kind="{kind}"}} {value}'
            )
        )

    stage_b = summary.get("stage_b_smoke", {})
    smoke_ok = stage_b.get("ok")
    doctrine_ok = stage_b.get("doctrine_ok") if smoke_ok else False
    lines.extend(
        [
            (
                "# HELP stage_b_rehearsal_stage_b_smoke_success "
                "Stage B smoke success (1=ok)"
            ),
            "# TYPE stage_b_rehearsal_stage_b_smoke_success gauge",
            f"stage_b_rehearsal_stage_b_smoke_success {_bool_to_int(smoke_ok)}",
            (
                "# HELP stage_b_rehearsal_stage_b_smoke_doctrine_ok "
                "Doctrine compliance from Stage B smoke (1=ok)"
            ),
            "# TYPE stage_b_rehearsal_stage_b_smoke_doctrine_ok gauge",
            f"stage_b_rehearsal_stage_b_smoke_doctrine_ok {_bool_to_int(doctrine_ok)}",
        ]
    )

    rotation = summary.get("rotation_drills", {})
    rotation_ok = rotation.get("ok")
    lines.extend(
        [
            (
                "# HELP stage_b_rehearsal_rotation_status "
                "Credential rotation coverage (1=ok)"
            ),
            "# TYPE stage_b_rehearsal_rotation_status gauge",
            f"stage_b_rehearsal_rotation_status {_bool_to_int(rotation_ok)}",
        ]
    )

    total_entries = rotation.get("total_entries")
    if isinstance(total_entries, int):
        lines.append(f"stage_b_rehearsal_rotation_entries_total {total_entries}")

    new_entries = rotation.get("new_entries") or []
    lines.append(f"stage_b_rehearsal_rotation_entries_recorded {len(new_entries)}")

    missing = set(rotation.get("missing") or [])
    expected = rotation.get("expected") or []
    for connector_id in expected:
        value = 0 if connector_id in missing else 1
        lines.append(
            (
                'stage_b_rehearsal_rotation_entry{connector_id="'
                f'{connector_id}"}} {value}'
            )
        )

    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _ensure_artifact_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Stage B rehearsal automation with connector health probes."
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=ARTIFACT_ROOT,
        help=(
            "Directory where rehearsal artifacts are stored (default: "
            "monitoring/stage_b)."
        ),
    )
    parser.add_argument(
        "--skip-health-checks",
        action="store_true",
        help="Do not execute connector and remote agent health probes.",
    )
    parser.add_argument(
        "--skip-stage-b-smoke",
        action="store_true",
        help="Skip Stage B smoke automation (rotation timestamps will not update).",
    )
    parser.add_argument(
        "--skip-remote",
        dest="include_remote",
        action="store_false",
        help="Skip remote agent probes when running health checks.",
    )
    parser.set_defaults(include_remote=True)
    return parser


def _summarise_rotation_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for entry in entries:
        summary.append(
            {
                "connector_id": entry.get("connector_id"),
                "rotated_at": entry.get("rotated_at"),
                "window_hours": entry.get("window_hours"),
            }
        )
    return summary


def _update_latest(run_files: Dict[str, Path], latest_dir: Path) -> None:
    latest_dir.mkdir(parents=True, exist_ok=True)
    for path in run_files.values():
        destination = latest_dir / path.name
        destination.write_bytes(path.read_bytes())


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    artifact_root = args.artifact_root
    if not artifact_root.is_absolute():
        artifact_root = REPO_ROOT / artifact_root

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = _ensure_artifact_dir(artifact_root / run_id)
    generated_at = _iso_now()

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "generated_at": generated_at,
        "artifact_dir": _relative_path(run_dir),
    }

    # Health checks
    health_results: Dict[str, bool] = {}
    if args.skip_health_checks:
        LOGGER.info("Skipping connector health checks")
        health_summary = {"ok": None, "results": [], "raw": {}, "skipped": True}
    else:
        health_results = health_check_connectors.run_health_checks(
            include_remote=args.include_remote
        )
        health_summary = summarise_health_results(health_results)
    summary["health_checks"] = health_summary

    health_payload = {
        "generated_at": generated_at,
        "include_remote": args.include_remote,
        **health_summary,
    }
    health_path = run_dir / HEALTH_FILENAME
    _write_json(health_path, health_payload)

    # Stage B smoke and rotation entries
    rotation_before = _load_rotation_entries(ROTATION_LOG)
    stage_b_payload: Dict[str, Any]
    stage_b_ok: bool | None
    doctrine_ok: bool | None
    if args.skip_stage_b_smoke:
        LOGGER.info("Skipping Stage B smoke automation")
        stage_b_ok = None
        doctrine_ok = None
        stage_b_payload = {"skipped": True}
    else:
        from scripts import stage_b_smoke  # Local import avoids optional dependencies

        try:
            stage_b_result = asyncio.run(stage_b_smoke.run_stage_b_smoke())
            stage_b_ok = True
            doctrine_ok = bool(stage_b_result.get("doctrine_ok"))
            stage_b_payload = stage_b_result
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Stage B smoke automation failed: %s", exc)
            stage_b_ok = False
            doctrine_ok = False
            stage_b_payload = {"error": str(exc)}

    rotation_after = _load_rotation_entries(ROTATION_LOG)
    new_rotation_entries = extract_new_rotation_entries(rotation_before, rotation_after)
    rotation_summary = _summarise_rotation_entries(new_rotation_entries)
    recorded_ids = {
        entry.get("connector_id")
        for entry in new_rotation_entries
        if entry.get("connector_id")
    }
    missing = [
        connector
        for connector in EXPECTED_ROTATION_CONNECTORS
        if connector not in recorded_ids
    ]
    rotation_ok = bool(new_rotation_entries) and not missing

    stage_b_section = {
        "ok": stage_b_ok,
        "doctrine_ok": doctrine_ok,
        "result": stage_b_payload,
    }
    summary["stage_b_smoke"] = stage_b_section

    rotation_section = {
        "ok": rotation_ok if stage_b_ok is not None else None,
        "new_entries": rotation_summary,
        "total_entries": len(rotation_after),
        "missing": missing,
        "expected": list(EXPECTED_ROTATION_CONNECTORS),
    }
    summary["rotation_drills"] = rotation_section

    checks = [
        value
        for value in (health_summary.get("ok"), stage_b_ok, rotation_section.get("ok"))
        if value is not None
    ]
    summary["overall_ok"] = bool(checks) and all(checks)

    summary["artifacts"] = {
        "health_checks": _relative_path(health_path),
        "stage_b_smoke": _relative_path(run_dir / STAGE_B_FILENAME),
        "rotation_drills": _relative_path(run_dir / ROTATION_FILENAME),
        "summary": _relative_path(run_dir / SUMMARY_FILENAME),
        "prometheus": _relative_path(run_dir / PROMETHEUS_FILENAME),
    }

    stage_b_path = run_dir / STAGE_B_FILENAME
    rotation_path = run_dir / ROTATION_FILENAME
    _write_json(stage_b_path, stage_b_payload)
    _write_json(
        rotation_path,
        {"generated_at": generated_at, "entries": rotation_summary},
    )

    summary_path = run_dir / SUMMARY_FILENAME
    _write_json(summary_path, summary)

    prom_path = run_dir / PROMETHEUS_FILENAME
    prom_path.write_text(render_prometheus_metrics(summary), encoding="utf-8")

    _update_latest(
        {"summary": summary_path, "prometheus": prom_path}, artifact_root / "latest"
    )

    print(json.dumps(summary, indent=2))

    return 0 if summary.get("overall_ok") else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())


__all__ = [
    "extract_new_rotation_entries",
    "render_prometheus_metrics",
    "main",
]
