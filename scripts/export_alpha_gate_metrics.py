#!/usr/bin/env python3
"""Export Alpha gate timings, success flags, and coverage metrics."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROM_PATH = REPO_ROOT / "monitoring" / "alpha_gate.prom"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "monitoring" / "alpha_gate_summary.json"


@dataclass
class PhaseRecord:
    """Structured representation of an Alpha gate phase."""

    name: str
    start_epoch: Optional[int]
    end_epoch: Optional[int]
    exit_code: Optional[int]
    skipped: bool

    def duration(self) -> Optional[int]:
        if self.start_epoch is None or self.end_epoch is None:
            return None
        return max(0, self.end_epoch - self.start_epoch)

    def success(self) -> Optional[bool]:
        if self.skipped:
            return False
        if self.exit_code is None:
            return None
        return self.exit_code == 0

    def to_summary(self) -> Dict[str, Any]:
        return {
            "start_epoch": self.start_epoch,
            "start": isoformat_or_none(self.start_epoch),
            "end_epoch": self.end_epoch,
            "end": isoformat_or_none(self.end_epoch),
            "duration_seconds": self.duration(),
            "exit_code": self.exit_code,
            "skipped": self.skipped,
            "success": self.success(),
        }


def isoformat_or_none(epoch: Optional[int]) -> Optional[str]:
    if epoch is None:
        return None
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_phase_argument(value: str) -> PhaseRecord:
    parts = value.split(":")
    if len(parts) != 5:
        raise argparse.ArgumentTypeError(
            "phase specification must be name:start:end:exit_code:skipped"
        )
    name, start, end, exit_code, skipped = parts
    start_epoch = int(start) if start else None
    end_epoch = int(end) if end else None
    exit_code_value = int(exit_code) if exit_code else None
    skipped_flag = skipped.lower() in {"1", "true", "yes", "on"}
    return PhaseRecord(
        name=name,
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        exit_code=exit_code_value,
        skipped=skipped_flag,
    )


def load_coverage(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"failed to decode coverage JSON at {path}: {exc}") from exc
    totals = payload.get("totals") or {}
    percent = totals.get("percent_covered")
    if percent is None and totals:
        covered = totals.get("covered_lines")
        statements = totals.get("num_statements")
        if covered is not None and statements:
            percent = round((covered / statements) * 100, 2)
    coverage_summary: Dict[str, Any] = {
        "percent": percent,
        "covered_lines": totals.get("covered_lines"),
        "num_statements": totals.get("num_statements"),
        "missing_lines": totals.get("missing_lines"),
    }
    return {k: v for k, v in coverage_summary.items() if v is not None}


def build_registry(
    phases: Iterable[PhaseRecord],
    coverage: Dict[str, Any],
    replay_summary: Optional[Dict[str, Any]] = None,
) -> CollectorRegistry:
    registry = CollectorRegistry()
    start_metric = Gauge(
        "alpha_gate_phase_start_timestamp_seconds",
        "UTC start time for an Alpha gate phase (seconds since epoch).",
        ["phase"],
        registry=registry,
    )
    end_metric = Gauge(
        "alpha_gate_phase_end_timestamp_seconds",
        "UTC completion time for an Alpha gate phase (seconds since epoch).",
        ["phase"],
        registry=registry,
    )
    duration_metric = Gauge(
        "alpha_gate_phase_duration_seconds",
        "Elapsed seconds per Alpha gate phase.",
        ["phase"],
        registry=registry,
    )
    success_metric = Gauge(
        "alpha_gate_phase_success",
        "1 when the Alpha gate phase succeeded, 0 when it failed or was skipped.",
        ["phase"],
        registry=registry,
    )
    exit_code_metric = Gauge(
        "alpha_gate_phase_exit_code",
        "Exit code reported by each Alpha gate phase.",
        ["phase"],
        registry=registry,
    )
    skipped_metric = Gauge(
        "alpha_gate_phase_skipped",
        "1 when the Alpha gate phase was explicitly skipped.",
        ["phase"],
        registry=registry,
    )

    all_success = True
    for phase in phases:
        if phase.start_epoch is not None:
            start_metric.labels(phase=phase.name).set(float(phase.start_epoch))
        if phase.end_epoch is not None:
            end_metric.labels(phase=phase.name).set(float(phase.end_epoch))
        duration = phase.duration()
        if duration is not None:
            duration_metric.labels(phase=phase.name).set(float(duration))
        phase_success = phase.success()
        if phase_success is None:
            all_success = False
            success_metric.labels(phase=phase.name).set(0)
        else:
            if not phase_success:
                all_success = False
            success_metric.labels(phase=phase.name).set(1 if phase_success else 0)
        if phase.exit_code is not None:
            exit_code_metric.labels(phase=phase.name).set(float(phase.exit_code))
        skipped_value = 1 if phase.skipped else 0
        skipped_metric.labels(phase=phase.name).set(skipped_value)

    overall_metric = Gauge(
        "alpha_gate_overall_success",
        "1 when all executed Alpha gate phases succeeded.",
        registry=registry,
    )
    overall_metric.set(1 if all_success else 0)

    if coverage:
        percent = coverage.get("percent")
        if percent is not None:
            Gauge(
                "alpha_gate_coverage_percent",
                "Line coverage percentage captured during Alpha gate tests.",
                registry=registry,
            ).set(float(percent))
        if "covered_lines" in coverage:
            Gauge(
                "alpha_gate_coverage_lines_covered",
                "Covered lines reported by coverage.py during the Alpha gate run.",
                registry=registry,
            ).set(float(coverage["covered_lines"]))
        if "num_statements" in coverage:
            Gauge(
                "alpha_gate_coverage_statements",
                "Total measured statements during the Alpha gate run.",
                registry=registry,
            ).set(float(coverage["num_statements"]))
        if "missing_lines" in coverage:
            Gauge(
                "alpha_gate_coverage_missing_lines",
                "Missing lines reported by coverage.py during the Alpha gate run.",
                registry=registry,
            ).set(float(coverage["missing_lines"]))

    if replay_summary:
        divergences = replay_summary.get("divergences")
        if divergences is not None:
            Gauge(
                "crown_replay_divergences_total",
                "Number of replay divergences detected during Crown regression.",
                registry=registry,
            ).set(float(divergences))
        duration = replay_summary.get("duration_seconds")
        if duration is not None:
            Gauge(
                "crown_replay_duration_seconds",
                "Elapsed seconds spent replaying recorded Crown scenarios.",
                registry=registry,
            ).set(float(duration))
        scenarios = replay_summary.get("scenarios")
        if scenarios is not None:
            Gauge(
                "crown_replay_scenarios_total",
                "Total recorded scenarios exercised during replay regression.",
                registry=registry,
            ).set(float(scenarios))

    return registry


def write_summary(
    path: Path,
    phases: Iterable[PhaseRecord],
    coverage: Dict[str, Any],
    replay_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    summary = {
        "generated_at": isoformat_or_none(
            int(datetime.now(tz=timezone.utc).timestamp())
        ),
        "phases": {phase.name: phase.to_summary() for phase in phases},
        "coverage": coverage or None,
        "replay": replay_summary or None,
    }
    all_success = True
    for phase in phases:
        phase_success = phase.success()
        if phase_success is None:
            all_success = False
        elif not phase_success:
            all_success = False
    summary["overall_success"] = all_success
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def load_replay_summary(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"failed to decode Crown replay summary at {path}: {exc}"
        ) from exc
    return data


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export Alpha gate metrics for Prometheus scraping."
    )
    parser.add_argument(
        "--phase",
        dest="phases",
        action="append",
        type=parse_phase_argument,
        help="Phase specification in the form name:start:end:exit_code:skipped",
    )
    parser.add_argument(
        "--coverage-json",
        type=Path,
        default=REPO_ROOT / "coverage.json",
        help="Path to coverage.json produced by coverage.py (optional).",
    )
    parser.add_argument(
        "--prom-path",
        type=Path,
        default=DEFAULT_PROM_PATH,
        help="Destination path for the Prometheus textfile exporter output.",
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help="Path to write the structured Alpha gate summary JSON.",
    )
    parser.add_argument(
        "--replay-summary",
        type=Path,
        default=None,
        help="Optional path to the Crown replay summary JSON.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    phases: list[PhaseRecord] = args.phases or []
    phases.sort(key=lambda record: record.name)
    coverage = load_coverage(args.coverage_json)
    replay_summary = load_replay_summary(args.replay_summary)

    registry = build_registry(phases, coverage, replay_summary)
    args.prom_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_textfile(str(args.prom_path), registry)

    write_summary(args.summary_path, phases, coverage, replay_summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
