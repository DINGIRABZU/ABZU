"""Benchmark concurrent memory queries across layers.

Results are written to ``data/benchmarks/query_memory.csv``.
"""

from __future__ import annotations

import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
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
) -> List[Tuple[str, float]]:
    """Run ``query_memory`` concurrently and return durations per query."""
    if queries is None:
        queries = ["alpha", "beta", "gamma", "delta", "epsilon"]
    results: List[Tuple[str, float]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_query = {ex.submit(_timed_query, q): q for q in queries}
        for future in as_completed(future_to_query):
            q = future_to_query[future]
            duration = future.result()
            results.append((q, duration))
    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "query_memory.csv"
    with out_file.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["query", "duration_s"])
        for q, d in results:
            writer.writerow([q, f"{d:.4f}"])
    return results


def main() -> None:
    results = benchmark_query_memory()
    for q, d in results:
        print(f"{q}: {d:.4f}s")


if __name__ == "__main__":
    main()
