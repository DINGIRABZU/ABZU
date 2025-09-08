"""Benchmark concurrent memory queries.

This script issues multiple ``query_memory`` calls in parallel to simulate
searches across memory layers. Per-query durations are written to
``data/benchmarks/query_memory.csv`` and aggregate metrics are stored in
``data/benchmarks/query_memory.json``.
"""

from __future__ import annotations

import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Tuple
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from memory.query_memory import query_memory


def _timed_query(text: str) -> float:
    start = time.perf_counter()
    query_memory(text)
    return time.perf_counter() - start


def benchmark_query_memory(
    queries: Iterable[str] | None = None, workers: int = 4
) -> dict[str, float]:
    """Run ``query_memory`` concurrently and return throughput/latency stats."""

    if queries is None:
        queries = ["alpha", "beta", "gamma", "delta", "epsilon"]

    start_all = time.perf_counter()
    results: List[Tuple[str, float]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_query = {ex.submit(_timed_query, q): q for q in queries}
        for future in as_completed(future_to_query):
            q = future_to_query[future]
            duration = future.result()
            results.append((q, duration))
    total_time = time.perf_counter() - start_all

    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)

    # write per-query durations
    out_csv = out_dir / "query_memory.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["query", "duration_s"])
        for q, d in results:
            writer.writerow([q, f"{d:.4f}"])

    durations = [d for _, d in results]
    throughput = len(results) / total_time if total_time else 0.0
    avg_latency = mean(durations) if durations else 0.0
    metrics = {
        "throughput_qps": round(throughput, 2),
        "avg_latency_s": round(avg_latency, 4),
    }

    out_json = out_dir / "query_memory.json"
    out_json.write_text(json.dumps(metrics) + "\n")

    return metrics


def main() -> None:
    metrics = benchmark_query_memory()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
