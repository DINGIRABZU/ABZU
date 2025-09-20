"""Regression tests for vector memory scaling benchmarks."""

from __future__ import annotations

import json
from pathlib import Path

from monitoring.vector_memory_scaling import BenchmarkRecord, benchmark_mode

TARGET_QUERY_P95 = 0.120
SUBSET_SIZE = 1024
QUERY_COUNT = 25


def _load_corpus() -> list[str]:
    metrics_path = Path("data/vector_memory_scaling/latency_metrics.json")
    with metrics_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    corpus_path = Path(payload["corpus_file"])
    with corpus_path.open("r", encoding="utf-8") as handle:
        corpus = [line.strip().split("\t", 1)[1] for line in handle]
    return corpus


def _load_metrics() -> list[dict]:
    metrics_path = Path("data/vector_memory_scaling/latency_metrics.json")
    with metrics_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["metrics"]


def _replay_mode(mode: str, corpus: list[str]) -> BenchmarkRecord:
    subset = corpus[:SUBSET_SIZE]
    return benchmark_mode(mode, subset, query_count=QUERY_COUNT)


def test_latency_targets_hold() -> None:
    corpus = _load_corpus()
    metrics = _load_metrics()
    for record in metrics:
        assert record["query_latency"]["p95"] <= TARGET_QUERY_P95
        replay = _replay_mode(record["mode"], corpus)
        assert replay.query_latency.p95 <= TARGET_QUERY_P95
        assert replay.write_latency.p95 < 0.020
