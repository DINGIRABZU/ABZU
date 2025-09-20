"""Utilities to benchmark vector memory ingestion and query latency."""

from __future__ import annotations

import importlib
import json
import logging
import random
import sys
import types
from dataclasses import dataclass, asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Callable, Dict, Iterable, List, Sequence

import numpy as np

LOGGER = logging.getLogger(__name__)


@dataclass
class LatencyStats:
    """Summary statistics for latency samples."""

    count: int
    p50: float
    p95: float
    max: float


@dataclass
class BenchmarkRecord:
    """Captured metrics for a benchmark run."""

    mode: str
    corpus_size: int
    query_count: int
    write_latency: LatencyStats
    query_latency: LatencyStats
    duration_seconds: float


def _compute_percentiles(samples: Sequence[float]) -> LatencyStats:
    if not samples:
        raise ValueError("samples cannot be empty")
    arr = np.asarray(samples, dtype=float)
    return LatencyStats(
        count=len(samples),
        p50=float(np.percentile(arr, 50)),
        p95=float(np.percentile(arr, 95)),
        max=float(arr.max()),
    )


def _install_faiss_stub() -> None:
    """Install a minimal FAISS stub so the fast path can be exercised."""

    class IndexFlatL2:
        def __init__(self, dim: int) -> None:
            self.dim = dim
            self._vectors = np.empty((0, dim), dtype=np.float32)

        def add(self, matrix: np.ndarray) -> None:
            if matrix.ndim != 2 or matrix.shape[1] != self.dim:
                raise ValueError("matrix shape mismatch")
            if not np.issubdtype(matrix.dtype, np.floating):
                matrix = matrix.astype(np.float32)
            self._vectors = np.vstack([self._vectors, matrix.astype(np.float32)])

        def search(self, queries: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
            if self._vectors.size == 0:
                dist = np.full((queries.shape[0], k), np.inf, dtype=np.float32)
                idx = np.full((queries.shape[0], k), -1, dtype=np.int32)
                return dist, idx
            queries = queries.astype(np.float32)
            diff = self._vectors[None, :, :] - queries[:, None, :]
            dists = np.sqrt((diff**2).sum(axis=2))
            idx = np.argsort(dists, axis=1)[:, :k]
            sorted_dists = np.take_along_axis(dists, idx, axis=1)
            return sorted_dists.astype(np.float32), idx.astype(np.int32)

        def reconstruct(self, index: int) -> np.ndarray:
            return self._vectors[index]

    stub = types.SimpleNamespace(IndexFlatL2=IndexFlatL2)
    sys.modules["faiss"] = stub


def _load_vector_memory(use_faiss_stub: bool):
    """Load :mod:`vector_memory` with an optional FAISS stub installed."""

    modules_to_clear = [
        name
        for name in list(sys.modules)
        if name.startswith("vector_memory") or name.startswith("memory_store")
    ]
    for name in modules_to_clear:
        del sys.modules[name]
    if use_faiss_stub:
        _install_faiss_stub()
    else:
        sys.modules.pop("faiss", None)
    return importlib.import_module("vector_memory")


def _fake_embedder(dim: int = 64) -> Callable[[str], Iterable[float]]:
    seeds: Dict[str, np.ndarray] = {}

    def embed(text: str) -> Iterable[float]:
        if text not in seeds:
            # derive a deterministic seed from the text for repeatability
            seed_val = abs(hash(text)) % (2**32)
            rng_local = np.random.default_rng(seed_val)
            seeds[text] = rng_local.random(dim, dtype=np.float32)
        return seeds[text]

    return embed


def _measure_latency(func: Callable[[], None]) -> float:
    start = perf_counter()
    func()
    return perf_counter() - start


def _benchmark_mode(
    mode: str,
    corpus: Sequence[str],
    *,
    use_faiss_stub: bool,
    query_count: int,
    embed_dim: int,
) -> BenchmarkRecord:
    vm = _load_vector_memory(use_faiss_stub)
    embedder = _fake_embedder(embed_dim)
    with TemporaryDirectory() as tmpdir:
        vm.configure(
            db_path=Path(tmpdir) / "db",
            embedder=embedder,
            shards=1,
            snapshot_interval=len(corpus) + 1,
            decay_strategy="none",
        )
        writes: List[float] = []
        start_run = perf_counter()
        for text in corpus:
            meta = {"mode": mode, "source": "benchmark"}
            writes.append(_measure_latency(lambda: vm.add_vector(text, meta)))
        population = list(corpus)
        sample_size = min(query_count, len(population))
        indices = random.Random(1337).sample(range(len(population)), k=sample_size)
        query_samples = [population[idx] for idx in indices]
        queries: List[float] = []
        for text in query_samples:
            queries.append(
                _measure_latency(lambda: vm.search(text, k=5, scoring="similarity"))
            )
        duration = perf_counter() - start_run
    write_stats = _compute_percentiles(writes)
    query_stats = _compute_percentiles(queries)
    LOGGER.info(
        "mode=%s writes(p95=%.6f) queries(p95=%.6f) duration=%.2fs",
        mode,
        write_stats.p95,
        query_stats.p95,
        duration,
    )
    return BenchmarkRecord(
        mode=mode,
        corpus_size=len(corpus),
        query_count=len(query_samples),
        write_latency=write_stats,
        query_latency=query_stats,
        duration_seconds=duration,
    )


def run_benchmark(
    *,
    corpus_size: int = 10_000,
    query_count: int = 200,
    embed_dim: int = 64,
    output_path: Path | None = None,
) -> List[BenchmarkRecord]:
    """Execute benchmarks for both standard and fallback storage paths."""

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    corpus_dir = Path("data/vector_memory_scaling")
    corpus_dir.mkdir(parents=True, exist_ok=True)
    corpus_file = corpus_dir / "corpus.jsonl"
    if not corpus_file.exists():
        rng = random.Random(42)
        with corpus_file.open("w", encoding="utf-8") as handle:
            for idx in range(corpus_size):
                words = [
                    rng.choice(
                        [
                            "aurora",
                            "quantum",
                            "memory",
                            "spiral",
                            "lattice",
                            "vector",
                            "inanna",
                            "chrono",
                            "echo",
                            "synthesis",
                        ]
                    )
                    for _ in range(8)
                ]
                handle.write(f"{idx}\t{' '.join(words)}\n")
    with corpus_file.open("r", encoding="utf-8") as handle:
        corpus = [line.strip().split("\t", 1)[1] for line in handle]
    results: List[BenchmarkRecord] = []
    standard = _benchmark_mode(
        "vector_memory",
        corpus,
        use_faiss_stub=True,
        query_count=query_count,
        embed_dim=embed_dim,
    )
    results.append(standard)
    fallback = _benchmark_mode(
        "memory_store_fallback",
        corpus,
        use_faiss_stub=False,
        query_count=query_count,
        embed_dim=embed_dim,
    )
    results.append(fallback)
    output = output_path or (corpus_dir / "latency_metrics.json")
    payload = {
        "corpus_file": str(corpus_file),
        "metrics": [
            {
                **asdict(record),
                "write_latency": asdict(record.write_latency),
                "query_latency": asdict(record.query_latency),
            }
            for record in results
        ],
    }
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    LOGGER.info("wrote metrics to %s", output)
    return results


__all__ = ["run_benchmark", "BenchmarkRecord", "LatencyStats"]


def benchmark_mode(
    mode: str,
    corpus: Sequence[str],
    *,
    query_count: int = 50,
    embed_dim: int = 64,
) -> BenchmarkRecord:
    """Benchmark a single storage mode for ad-hoc validation runs."""

    use_faiss_stub = mode == "vector_memory"
    return _benchmark_mode(
        mode,
        corpus,
        use_faiss_stub=use_faiss_stub,
        query_count=query_count,
        embed_dim=embed_dim,
    )


__all__.append("benchmark_mode")
