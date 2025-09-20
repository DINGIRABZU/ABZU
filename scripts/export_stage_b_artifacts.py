#!/usr/bin/env python3
"""Collect Stage B rehearsal logs and metrics for readiness review."""

from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_ROOT = REPO_ROOT / "logs"
STAGE_B_LOG_ROOT = LOG_ROOT / "stage_b"
MONITORING_ROOT = REPO_ROOT / "monitoring"
STAGE_B_MONITORING_ROOT = MONITORING_ROOT / "stage_b"
ROTATION_LOG = LOG_ROOT / "stage_b_rotation_drills.jsonl"
VECTOR_METRICS_PATH = (
    REPO_ROOT / "data" / "vector_memory_scaling" / "latency_metrics.json"
)
VECTOR_LOG_PATH = REPO_ROOT / "data" / "vector_memory.log"
CORPUS_PATH = REPO_ROOT / "data" / "vector_memory_scaling" / "corpus.jsonl"
HARDWARE_DOC = REPO_ROOT / "docs" / "hardware_support.md"

ENV_SNAPSHOT_KEYS = (
    "ABZU_USE_MCP",
    "NEOABZU_VECTOR_SHARDS",
    "AUDIO_BACKEND",
    "MCP_GATEWAY_URL",
    "VECTOR_MEMORY_DECAY_STRATEGY",
    "VECTOR_MEMORY_DECAY_SECONDS",
    "VECTOR_MEMORY_DECAY_THRESHOLD",
)


@dataclass(frozen=True)
class FileMetadata:
    path: str
    exists: bool
    size_bytes: int | None
    modified_at: str | None


@dataclass(frozen=True)
class RotationSummary:
    total_entries: int
    connectors: list[str]
    first_rotation: dict[str, Any] | None
    latest_rotation: dict[str, Any] | None


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _format_epoch(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return (
        datetime.fromtimestamp(epoch, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def describe_file(path: Path) -> FileMetadata:
    if path.exists():
        stat = path.stat()
        return FileMetadata(
            path=_relative_path(path),
            exists=True,
            size_bytes=stat.st_size,
            modified_at=_format_epoch(stat.st_mtime),
        )
    return FileMetadata(
        path=_relative_path(path),
        exists=False,
        size_bytes=None,
        modified_at=None,
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    return records


def summarise_rotations(records: Iterable[dict[str, Any]]) -> RotationSummary:
    entries = list(records)
    connectors = sorted(
        {entry.get("connector_id", "") for entry in entries if "connector_id" in entry}
    )
    first = entries[0] if entries else None
    latest = entries[-1] if entries else None
    return RotationSummary(
        total_entries=len(entries),
        connectors=connectors,
        first_rotation=first,
        latest_rotation=latest,
    )


def count_lines(path: Path) -> int | None:
    if not path.exists():
        return None
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for count, _ in enumerate(handle, start=1):
            pass
    return count


def _parse_stage_a_hardware() -> dict[str, Any]:
    if not HARDWARE_DOC.exists():
        return {}
    components: dict[str, str] = {}
    runtime_flags: list[str] = []
    capture_table = False
    capture_flags = False
    with HARDWARE_DOC.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if line.startswith("## Stage") and "Runner Profile" in line:
                capture_table = False
                components.clear()
                continue
            if line.startswith("## ") and "Runner Profile" not in line and components:
                break
            if line.startswith("| Component |"):
                capture_table = True
                continue
            if capture_table:
                if line.startswith("| ---"):
                    continue
                if not line.startswith("|"):
                    if not line.strip():
                        continue
                    if line.startswith("### Runtime Flags"):
                        capture_table = False
                        capture_flags = True
                    else:
                        capture_table = False
                    continue
                parts = [part.strip() for part in line.strip("|").split("|")]
                if len(parts) >= 2:
                    components[parts[0]] = parts[1]
                continue
            if line.startswith("### Runtime Flags"):
                capture_flags = True
                runtime_flags.clear()
                continue
            if capture_flags:
                if line.startswith("## "):
                    break
                if line.startswith("- "):
                    runtime_flags.append(line[2:].strip())
                elif not line.strip():
                    continue
                else:
                    capture_flags = False
    payload: dict[str, Any] = {}
    if components:
        payload["components"] = components
    if runtime_flags:
        payload["runtime_flags"] = runtime_flags
    return payload


def _parse_env_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in ENV_SNAPSHOT_KEYS:
        value = os.environ.get(key)
        snapshot[key] = value
    return snapshot


def _compute_stage_b_decay_settings(env_snapshot: dict[str, Any]) -> dict[str, Any]:
    decay_strategy = env_snapshot.get("VECTOR_MEMORY_DECAY_STRATEGY") or "none"
    decay_seconds = env_snapshot.get("VECTOR_MEMORY_DECAY_SECONDS")
    decay_threshold = env_snapshot.get("VECTOR_MEMORY_DECAY_THRESHOLD")
    return {
        "strategy": decay_strategy,
        "seconds": float(decay_seconds) if decay_seconds else None,
        "threshold": float(decay_threshold) if decay_threshold else None,
    }


def _parse_shard_count(env_snapshot: dict[str, Any]) -> int:
    raw_value = env_snapshot.get("NEOABZU_VECTOR_SHARDS")
    if not raw_value:
        return 1
    try:
        shards = int(raw_value)
    except ValueError:
        return 1
    return max(1, shards)


def _annotate_metrics(
    records: list[dict[str, Any]],
    *,
    shard_count: int,
    decay: dict[str, Any],
    collected_at: str,
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for record in records:
        payload = dict(record)
        payload["collected_at"] = collected_at
        payload["shards"] = shard_count
        payload["decay_strategy"] = decay["strategy"]
        payload["decay_seconds"] = decay.get("seconds")
        payload["decay_threshold"] = decay.get("threshold")
        annotated.append(payload)
    return annotated


def _build_metrics_prom_content(
    records: Iterable[dict[str, Any]],
    *,
    run_id: str,
    shard_count: int,
    decay: dict[str, Any],
) -> str:
    lines: list[str] = []
    help_defs = [
        (
            "stage_b_load_test_duration_seconds",
            "Total duration of Stage B load test runs.",
        ),
        (
            "stage_b_load_test_write_latency_p50_seconds",
            "Median write latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_write_latency_p95_seconds",
            "95th percentile write latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_write_latency_max_seconds",
            "Maximum write latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_query_latency_p50_seconds",
            "Median query latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_query_latency_p95_seconds",
            "95th percentile query latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_query_latency_max_seconds",
            "Maximum query latency recorded during Stage B load tests.",
        ),
        (
            "stage_b_load_test_corpus_size",
            "Corpus size evaluated during Stage B load tests.",
        ),
        (
            "stage_b_load_test_query_count",
            "Queries executed during Stage B load tests.",
        ),
    ]
    for name, description in help_defs:
        lines.append(f"# HELP {name} {description}")
        lines.append(f"# TYPE {name} gauge")
    decay_seconds_label = decay.get("seconds")
    decay_threshold_label = decay.get("threshold")
    for record in records:
        mode = record.get("mode", "unknown")
        labels = {
            "mode": str(mode),
            "run_id": run_id,
            "shards": str(shard_count),
            "decay_strategy": str(decay.get("strategy", "none")),
            "decay_seconds": (
                "unset" if decay_seconds_label is None else str(decay_seconds_label)
            ),
            "decay_threshold": (
                "unset" if decay_threshold_label is None else str(decay_threshold_label)
            ),
        }
        label_str = ",".join(
            f'{key}="{value}"' for key, value in sorted(labels.items())
        )
        _append_metric(
            lines,
            "stage_b_load_test_duration_seconds",
            label_str,
            record.get("duration_seconds", 0.0),
        )
        write_latency = record.get("write_latency", {})
        query_latency = record.get("query_latency", {})
        _append_metric(
            lines,
            "stage_b_load_test_write_latency_p50_seconds",
            label_str,
            write_latency.get("p50", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_write_latency_p95_seconds",
            label_str,
            write_latency.get("p95", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_write_latency_max_seconds",
            label_str,
            write_latency.get("max", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_query_latency_p50_seconds",
            label_str,
            query_latency.get("p50", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_query_latency_p95_seconds",
            label_str,
            query_latency.get("p95", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_query_latency_max_seconds",
            label_str,
            query_latency.get("max", 0.0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_corpus_size",
            label_str,
            record.get("corpus_size", 0),
        )
        _append_metric(
            lines,
            "stage_b_load_test_query_count",
            label_str,
            record.get("query_count", 0),
        )
    return "\n".join(lines) + "\n"


def _append_metric(lines: list[str], name: str, label_str: str, value: Any) -> None:
    lines.append(f"{name}{{{label_str}}} {value}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _update_latest_symlink(root: Path, run_id: str) -> None:
    latest = root / "latest"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(run_id)


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    collected_at = _utc_now_iso()

    stage_b_log_dir = STAGE_B_LOG_ROOT / run_id
    stage_b_monitor_dir = STAGE_B_MONITORING_ROOT / run_id
    stage_b_log_dir.mkdir(parents=True, exist_ok=False)
    stage_b_monitor_dir.mkdir(parents=True, exist_ok=False)

    rotation_records = load_jsonl(ROTATION_LOG)
    rotation_summary = summarise_rotations(rotation_records)

    env_snapshot = _parse_env_snapshot()
    decay_settings = _compute_stage_b_decay_settings(env_snapshot)
    shard_count = _parse_shard_count(env_snapshot)

    vector_metrics: dict[str, Any] = {}
    metrics_records: list[dict[str, Any]] = []
    vector_metrics_meta = describe_file(VECTOR_METRICS_PATH)
    if vector_metrics_meta.exists:
        with VECTOR_METRICS_PATH.open("r", encoding="utf-8") as handle:
            vector_metrics = json.load(handle)
        metrics_records = vector_metrics.get("metrics", [])
    annotated_metrics = _annotate_metrics(
        metrics_records,
        shard_count=shard_count,
        decay=decay_settings,
        collected_at=collected_at,
    )

    corpus_meta = describe_file(CORPUS_PATH)
    corpus_records = count_lines(CORPUS_PATH)

    ingestion_meta = describe_file(VECTOR_LOG_PATH)

    hardware_profile = _parse_stage_a_hardware()
    runtime_platform = platform.uname()._asdict()

    summary_payload = {
        "run_id": run_id,
        "collected_at": collected_at,
        "rotation_summary": {
            "total_entries": rotation_summary.total_entries,
            "connectors": rotation_summary.connectors,
            "first_rotation": rotation_summary.first_rotation,
            "latest_rotation": rotation_summary.latest_rotation,
        },
        "ingestion_log": ingestion_meta.__dict__,
        "corpus": {
            "metadata": corpus_meta.__dict__,
            "record_count": corpus_records,
        },
        "vector_memory_metrics": {
            "metadata": vector_metrics_meta.__dict__,
            "records": annotated_metrics,
        },
        "environment": env_snapshot,
        "memory_configuration": {
            "shards": shard_count,
            "decay": decay_settings,
        },
        "hardware_profile": {
            "canonical_stage_a": hardware_profile,
            "runtime_detected": runtime_platform,
        },
    }

    summary_path = stage_b_log_dir / "ingestion_vector_memory_summary.json"
    _write_json(summary_path, summary_payload)

    if ROTATION_LOG.exists():
        shutil.copy2(ROTATION_LOG, stage_b_log_dir / ROTATION_LOG.name)

    if ingestion_meta.exists:
        shutil.copy2(VECTOR_LOG_PATH, stage_b_log_dir / VECTOR_LOG_PATH.name)

    if vector_metrics_meta.exists:
        shutil.copy2(VECTOR_METRICS_PATH, stage_b_log_dir / VECTOR_METRICS_PATH.name)

    if corpus_meta.exists:
        shutil.copy2(CORPUS_PATH, stage_b_log_dir / CORPUS_PATH.name)

    prom_content = _build_metrics_prom_content(
        annotated_metrics,
        run_id=run_id,
        shard_count=shard_count,
        decay=decay_settings,
    )
    prom_path = stage_b_monitor_dir / "stage_b_load_test.prom"
    _write_text(prom_path, prom_content)

    summary_monitor_payload = {
        "run_id": run_id,
        "generated_at": collected_at,
        "environment": env_snapshot,
        "memory_configuration": {
            "shards": shard_count,
            "decay": decay_settings,
        },
        "latency_metrics": annotated_metrics,
        "hardware_profile": {
            "canonical_stage_a": hardware_profile,
            "runtime_detected": runtime_platform,
        },
    }
    monitor_summary_path = stage_b_monitor_dir / "load_test_summary.json"
    _write_json(monitor_summary_path, summary_monitor_payload)

    shutil.copy2(prom_path, stage_b_log_dir / prom_path.name)
    shutil.copy2(monitor_summary_path, stage_b_log_dir / monitor_summary_path.name)

    _update_latest_symlink(STAGE_B_LOG_ROOT, run_id)
    _update_latest_symlink(STAGE_B_MONITORING_ROOT, run_id)

    print(f"Stage B artifacts exported to {stage_b_log_dir} and {stage_b_monitor_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
