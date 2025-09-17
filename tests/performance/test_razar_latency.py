"""Performance guardrails for RAZAR escalation latency."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import bench_razar_escalation as bench  # noqa: E402


def test_escalation_latency_percentiles():
    result = bench.run_benchmark(seed=1337)
    latencies = result.all_agent_latencies
    assert latencies, "benchmark should yield latency samples"

    p90 = bench.compute_percentile(latencies, 90)
    p95 = bench.compute_percentile(latencies, 95)
    p99 = bench.compute_percentile(latencies, 99)

    assert p90 <= 0.32
    assert p95 <= 0.34
    assert p99 <= 0.36
