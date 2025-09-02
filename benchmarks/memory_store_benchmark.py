"""Benchmark basic memory store operations."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from memory_store import MemoryStore


def benchmark_memory_store(entries: int = 1000, dim: int = 64) -> dict[str, float]:
    """Insert ``entries`` vectors and measure add/search performance."""
    store = MemoryStore(":memory:")
    vectors = [[float(i % 10) for _ in range(dim)] for i in range(entries)]

    start = time.perf_counter()
    for i, vec in enumerate(vectors):
        store.add(f"{i:032x}", vec, {})
    add_time = time.perf_counter() - start

    start = time.perf_counter()
    store.search([0.0] * dim, k=5)
    search_time = time.perf_counter() - start

    metrics = {
        "adds_per_sec": round(entries / add_time if add_time else 0.0, 2),
        "search_time": round(search_time, 4),
    }
    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "memory_store.json"
    out_file.write_text(json.dumps(metrics))
    return metrics


def main() -> None:
    metrics = benchmark_memory_store()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
