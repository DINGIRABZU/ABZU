"""Run a memory load proof against a 10k-record fixture.

This CLI initializes :class:`memory.bundle.MemoryBundle`, replays queries
from a JSONL fixture, records latency percentiles, and exports memory
initialization metrics for Stage B readiness reviews.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence


# Ensure the repository root is importable when the script is executed via a
# relative path such as ``python scripts/memory_load_proof.py``.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


from memory.bundle import MemoryBundle
from monitoring.boot_metrics import (  # noqa: E402  (delayed import)
    MemoryInitMetricValues,
    record_memory_init_metrics,
    summarize_memory_statuses,
)
from check_memory_layers import (  # noqa: E402  (delayed import)
    MemoryLayerCheckReport,
    verify_memory_layers,
)

logger = logging.getLogger("memory.load_proof")


@dataclass(frozen=True)
class LoadProofResult:
    """Aggregate results from a load-proof execution."""

    dataset: Path
    total_records: int
    queries_executed: int
    init_duration_s: float
    p50_latency_s: float
    p95_latency_s: float
    p99_latency_s: float
    layer_total: int
    layer_ready: int
    layer_failed: int
    query_failures: int
    stubbed: bool
    fallback_reason: str | None
    implementation: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay memory queries from a JSONL fixture and export latency "
            "percentiles for Stage B readiness."
        )
    )
    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the JSONL fixture containing memory queries.",
    )
    parser.add_argument(
        "--query-field",
        default="query",
        help=(
            "JSON key holding the query text. Fallbacks: 'prompt' and 'text' "
            "when the preferred field is missing."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of records to replay.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warm-up queries executed before timing begins.",
    )
    parser.add_argument(
        "--metrics-source",
        default="memory-load-proof",
        help=(
            "Source label applied to razar_memory_init_* gauges. Defaults to "
            "'memory-load-proof'."
        ),
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=None,
        help=(
            "Optional path for the Prometheus textfile exporter. When omitted "
            "the default boot metrics path is used."
        ),
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=Path("logs/memory_load_proof.jsonl"),
        help="JSONL file that receives the per-run summary.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args()


def _load_records(path: Path) -> Iterator[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                yield json.loads(text)
            except json.JSONDecodeError as exc:  # pragma: no cover - logging only
                logger.warning(
                    "Skipping malformed JSON on line %s: %s", line_number, exc
                )


def _extract_query(record: dict[str, object], preferred: str) -> str | None:
    candidates = [preferred, "prompt", "text"]
    for key in candidates:
        if key in record:
            value = record[key]
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
    return None


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    clipped = sorted(values)
    rank = (percentile / 100.0) * (len(clipped) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return clipped[int(rank)]
    weight = rank - lower
    return clipped[lower] + (clipped[upper] - clipped[lower]) * weight


def _record_metrics(
    *,
    source: str,
    duration_s: float,
    statuses: dict[str, object],
    output_path: Path | None,
) -> tuple[int, int, int]:
    total, ready, failed = summarize_memory_statuses(statuses)
    record_memory_init_metrics(
        MemoryInitMetricValues(
            duration_seconds=duration_s,
            layer_total=float(total),
            layer_ready=float(ready),
            layer_failed=float(failed),
            source=source,
            error=failed > 0,
        ),
        output_path=output_path,
    )
    return total, ready, failed


def run_load_proof(args: argparse.Namespace) -> LoadProofResult:
    bundle = MemoryBundle()
    bundle_stubbed = getattr(bundle, "stubbed", False)
    bundle_fallback = getattr(bundle, "fallback_reason", None)
    bundle_implementation = getattr(bundle, "implementation", "unknown")

    start_init = time.perf_counter()
    statuses = bundle.initialize()
    init_duration = time.perf_counter() - start_init

    bundle_stubbed = bool(getattr(bundle, "stubbed", bundle_stubbed))
    bundle_fallback = getattr(bundle, "fallback_reason", bundle_fallback)
    bundle_implementation = str(
        getattr(bundle, "implementation", bundle_implementation)
    )

    layer_total, layer_ready, layer_failed = _record_metrics(
        source=args.metrics_source,
        duration_s=init_duration,
        statuses=statuses,
        output_path=args.metrics_output,
    )

    records_iter = _load_records(args.dataset)
    queries: list[str] = []
    for record in records_iter:
        query = _extract_query(record, args.query_field)
        if query is None:
            continue
        queries.append(query)
        if args.limit is not None and len(queries) >= args.limit:
            break

    if not queries:
        raise ValueError(
            "No queries extracted from dataset. Check the --query-field option."
        )

    warmup = max(min(args.warmup, max(len(queries) - 1, 0)), 0)
    if warmup:
        for query in queries[:warmup]:
            try:
                bundle.query(query)
            except Exception:  # pragma: no cover - warmup best effort
                logger.exception("Warm-up query failed: %s", query)

    timed_queries = queries[warmup:] if warmup < len(queries) else queries

    latencies: list[float] = []
    query_failures = 0
    for query in timed_queries:
        start_query = time.perf_counter()
        try:
            result = bundle.query(query)
        except Exception:  # pragma: no cover - logged and counted
            elapsed = time.perf_counter() - start_query
            latencies.append(elapsed)
            query_failures += 1
            logger.exception("Query execution failed: %s", query)
            continue

        elapsed = time.perf_counter() - start_query
        latencies.append(elapsed)

        failed_layers = result.get("failed_layers") if isinstance(result, dict) else []
        if failed_layers:
            query_failures += 1

    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)

    return LoadProofResult(
        dataset=args.dataset,
        total_records=len(queries),
        queries_executed=len(timed_queries),
        init_duration_s=init_duration,
        p50_latency_s=p50,
        p95_latency_s=p95,
        p99_latency_s=p99,
        layer_total=layer_total,
        layer_ready=layer_ready,
        layer_failed=layer_failed,
        query_failures=query_failures,
        stubbed=bundle_stubbed,
        fallback_reason=bundle_fallback if isinstance(bundle_fallback, str) else None,
        implementation=bundle_implementation,
    )


def _append_pretest_report(
    report: MemoryLayerCheckReport,
    dataset: Path,
    log_path: Path,
    *,
    stubbed: bool,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset),
        "event": "memory-pretest",
        "layer_statuses": report.statuses,
        "optional_stubs": [
            {
                "layer": stub.layer,
                "module": stub.module,
                "reason": stub.reason,
            }
            for stub in report.optional_stubs
        ],
        "stubbed_bundle": stubbed,
        "bundle_implementation": report.bundle_implementation,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.write("\n")


def _run_pretest_hook(dataset: Path, log_path: Path) -> bool:
    report = verify_memory_layers()
    stub_suffixes = ("neoabzu_bundle", "neoabzu_stub")
    stubbed_modules = [
        stub for stub in report.optional_stubs if stub.module.endswith(stub_suffixes)
    ]
    stubbed = bool(stubbed_modules)
    unexpected = [
        stub
        for stub in report.optional_stubs
        if not stub.module.endswith(stub_suffixes)
    ]

    if report.optional_stubs:
        _append_pretest_report(report, dataset, log_path, stubbed=stubbed)

    if unexpected:
        stub_summary = ", ".join(f"{stub.layer}:{stub.module}" for stub in unexpected)
        logger.error(
            "Optional memory stubs detected during preflight: %s", stub_summary
        )
        raise RuntimeError(
            "Optional memory stubs detected. Halt load proof until primary layers"
            " are restored."
        )

    if stubbed:
        modules = ", ".join(f"{stub.layer}:{stub.module}" for stub in stubbed_modules)
        logger.warning(
            "Memory bundle running in stubbed mode – continuing",
            extra={
                "stubbed_layers": [stub.layer for stub in stubbed_modules],
                "stubbed_modules": [stub.module for stub in stubbed_modules],
            },
        )
        logger.info(
            "Stubbed bundle detected for %s layers; continuing pretest", modules
        )
    else:
        logger.info(
            "Memory layer preflight passed with %s layers", len(report.statuses)
        )
    return stubbed


def _append_log(result: LoadProofResult, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": str(result.dataset),
        "total_records": result.total_records,
        "queries_executed": result.queries_executed,
        "init_duration_s": round(result.init_duration_s, 6),
        "latency_p50_s": round(result.p50_latency_s, 6),
        "latency_p95_s": round(result.p95_latency_s, 6),
        "latency_p99_s": round(result.p99_latency_s, 6),
        "layer_total": result.layer_total,
        "layer_ready": result.layer_ready,
        "layer_failed": result.layer_failed,
        "query_failures": result.query_failures,
        "stubbed_bundle": result.stubbed,
        "fallback_reason": result.fallback_reason,
        "bundle_implementation": result.implementation,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.write("\n")


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    stubbed = _run_pretest_hook(args.dataset, args.log_path)
    result = run_load_proof(args)
    _append_log(result, args.log_path)

    logger.info(
        "Load proof complete: dataset=%s records=%s p95=%.3fms p99=%.3fms",
        result.dataset,
        result.total_records,
        result.p95_latency_s * 1000,
        result.p99_latency_s * 1000,
    )

    summary = {
        "dataset": str(result.dataset),
        "total_records": result.total_records,
        "queries_timed": result.queries_executed,
        "init_duration_s": round(result.init_duration_s, 6),
        "latency_p50_s": round(result.p50_latency_s, 6),
        "latency_p95_s": round(result.p95_latency_s, 6),
        "latency_p99_s": round(result.p99_latency_s, 6),
        "layers": {
            "total": result.layer_total,
            "ready": result.layer_ready,
            "failed": result.layer_failed,
        },
        "query_failures": result.query_failures,
        "stubbed_bundle": result.stubbed or stubbed,
        "fallback_reason": result.fallback_reason,
        "bundle_implementation": result.implementation,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
