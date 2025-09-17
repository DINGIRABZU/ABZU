"""Simulate RAZAR escalation bursts and summarise Prometheus metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from prometheus_client import REGISTRY

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from razar import metrics

DEFAULT_COMPONENT = "razar-escalation-service"
DEFAULT_AGENT = "razar-escalation-agent"
DEFAULT_OUTPUT = Path("docs/performance/razar_escalation.md")


@dataclass(frozen=True)
class BurstConfig:
    """Configuration for a single workload burst."""

    label: str
    invocations: int
    success_rate: float
    max_retries: int
    agent_latency_range: tuple[float, float]
    retry_latency_range: tuple[float, float]


@dataclass
class BurstResult:
    """Outcome metrics for a simulated burst."""

    label: str
    invocations: int
    successes: int
    failures: int
    retry_attempts: int
    agent_latencies: list[float]
    retry_durations: list[float]

    def percentile(self, value: float) -> float:
        return compute_percentile(self.agent_latencies, value)


@dataclass
class BenchmarkResult:
    """Aggregated benchmark outputs."""

    component: str
    agent: str
    bursts: list[BurstResult]
    samples: dict[str, float]
    generated_at: dt.datetime

    @property
    def all_agent_latencies(self) -> list[float]:
        latencies: list[float] = []
        for burst in self.bursts:
            latencies.extend(burst.agent_latencies)
        return latencies


DEFAULT_BURSTS: tuple[BurstConfig, ...] = (
    BurstConfig(
        label="warmup",
        invocations=30,
        success_rate=0.92,
        max_retries=1,
        agent_latency_range=(0.18, 0.30),
        retry_latency_range=(0.05, 0.12),
    ),
    BurstConfig(
        label="surge",
        invocations=60,
        success_rate=0.85,
        max_retries=2,
        agent_latency_range=(0.20, 0.34),
        retry_latency_range=(0.08, 0.18),
    ),
    BurstConfig(
        label="stabilisation",
        invocations=40,
        success_rate=0.9,
        max_retries=2,
        agent_latency_range=(0.17, 0.28),
        retry_latency_range=(0.06, 0.14),
    ),
)


def compute_percentile(samples: Iterable[float], percentile: float) -> float:
    """Return the percentile for ``samples`` using linear interpolation."""

    data = sorted(float(value) for value in samples)
    if not data:
        return 0.0

    clamped = min(max(percentile, 0.0), 100.0)
    if clamped == 0.0:
        return data[0]
    if clamped == 100.0:
        return data[-1]

    rank = (len(data) - 1) * (clamped / 100.0)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)
    lower = data[lower_index]
    upper = data[upper_index]
    if lower_index == upper_index:
        return lower
    weight = rank - lower_index
    return lower + (upper - lower) * weight


def _disable_metrics_server() -> None:
    """Prevent the HTTP metrics server from binding to a port."""

    if getattr(metrics, "start_http_server", None) is not None:
        metrics.start_http_server = lambda *args, **kwargs: None  # type: ignore[assignment]


def _get_sample(name: str, labels: dict[str, str]) -> float:
    value = REGISTRY.get_sample_value(name, labels)
    return 0.0 if value is None else float(value)


def collect_samples(component: str, agent: str) -> dict[str, float]:
    """Extract Prometheus samples for the configured component and agent."""

    return {
        "success_total": _get_sample(
            "razar_ai_invocation_success_total", {"component": component}
        ),
        "failure_total": _get_sample(
            "razar_ai_invocation_failure_total", {"component": component}
        ),
        "retry_total": _get_sample(
            "razar_ai_invocation_retries_total", {"component": component}
        ),
        "retry_sum": _get_sample(
            "razar_ai_retry_duration_seconds_sum", {"component": component}
        ),
        "retry_count": _get_sample(
            "razar_ai_retry_duration_seconds_count", {"component": component}
        ),
        "agent_sum": _get_sample(
            "razar_agent_call_duration_seconds_sum", {"agent": agent}
        ),
        "agent_count": _get_sample(
            "razar_agent_call_duration_seconds_count", {"agent": agent}
        ),
    }


def simulate_burst(
    component: str,
    agent: str,
    config: BurstConfig,
    rng: random.Random,
) -> BurstResult:
    """Run a single burst simulation and record Prometheus metrics."""

    successes = 0
    failures = 0
    retry_attempts = 0
    agent_latencies: list[float] = []
    retry_durations: list[float] = []

    for _ in range(config.invocations):
        success = rng.random() < config.success_rate
        retries = 0
        if success:
            successes += 1
        else:
            failures += 1
            if config.max_retries:
                retries = rng.randint(1, max(config.max_retries, 1))
        metrics.record_invocation(component, success, retries=retries)
        if retries:
            retry_attempts += retries
            retry_duration = 0.0
            for _ in range(retries):
                retry_duration += rng.uniform(*config.retry_latency_range)
            metrics.observe_retry_duration(component, retry_duration)
            retry_durations.append(retry_duration)
        latency = rng.uniform(*config.agent_latency_range)
        metrics.observe_agent_latency(agent, latency)
        agent_latencies.append(latency)

    return BurstResult(
        label=config.label,
        invocations=config.invocations,
        successes=successes,
        failures=failures,
        retry_attempts=retry_attempts,
        agent_latencies=agent_latencies,
        retry_durations=retry_durations,
    )


def run_benchmark(
    *,
    component: str = DEFAULT_COMPONENT,
    agent: str = DEFAULT_AGENT,
    bursts: Sequence[BurstConfig] | None = None,
    seed: int | None = None,
    enable_server: bool = False,
) -> BenchmarkResult:
    """Execute the benchmark and return collected metrics."""

    if not enable_server:
        _disable_metrics_server()

    if not metrics.init_metrics():
        raise RuntimeError(
            "prometheus_client is required for bench_razar_escalation; "
            "install dependencies"
        )

    rng = random.Random(seed)
    chosen_bursts = list(bursts or DEFAULT_BURSTS)
    component_label = component.lower()
    agent_label = agent.lower()
    baseline = collect_samples(component_label, agent_label)
    results = [
        simulate_burst(component, agent, config, rng) for config in chosen_bursts
    ]
    post = collect_samples(component_label, agent_label)
    samples = {
        key: post.get(key, 0.0) - baseline.get(key, 0.0)
        for key in post
    }
    return BenchmarkResult(
        component=component_label,
        agent=agent_label,
        bursts=results,
        samples=samples,
        generated_at=dt.datetime.now(dt.timezone.utc),
    )


def write_report(result: BenchmarkResult, output_path: Path) -> None:
    """Persist a markdown report for the benchmark result."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_invocations = sum(b.invocations for b in result.bursts)
    total_successes = sum(b.successes for b in result.bursts)
    total_failures = sum(b.failures for b in result.bursts)
    total_retries = sum(b.retry_attempts for b in result.bursts)

    aggregate_latencies = result.all_agent_latencies
    percentiles = {
        "p50": compute_percentile(aggregate_latencies, 50),
        "p90": compute_percentile(aggregate_latencies, 90),
        "p95": compute_percentile(aggregate_latencies, 95),
        "p99": compute_percentile(aggregate_latencies, 99),
    }

    lines = [
        "# RAZAR Escalation Load Simulation",
        "",
        f"_Generated on {result.generated_at:%Y-%m-%d %H:%M UTC}_",
        "",
        "## Scenario",
        "",
        f"- Component: `{result.component}`",
        f"- Agent: `{result.agent}`",
        f"- Total invocations: {total_invocations}",
        f"- Successes: {total_successes}",
        f"- Failures: {total_failures}",
        f"- Retry attempts: {total_retries}",
        "",
        "## Burst Latency Percentiles",
        "",
        (
            "| Burst | Invocations | Success rate | Failures | "
            "Retries | P50 (s) | P90 (s) | P95 (s) |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]

    for burst in result.bursts:
        success_rate = (
            (burst.successes / burst.invocations) if burst.invocations else 0.0
        )
        lines.append(
            (
                "| {label} | {invocations} | {success:.1%} | {failures} | "
                "{retries} | {p50:.3f} | {p90:.3f} | {p95:.3f} |"
            ).format(
                label=burst.label,
                invocations=burst.invocations,
                success=success_rate,
                failures=burst.failures,
                retries=burst.retry_attempts,
                p50=burst.percentile(50),
                p90=burst.percentile(90),
                p95=burst.percentile(95),
            )
        )

    lines.extend(
        [
            "",
            "## Aggregate Percentiles",
            "",
            "| Percentile | Latency (s) |",
            "|---|---|",
        ]
    )

    for label, value in percentiles.items():
        lines.append(f"| {label.upper()} | {value:.3f} |")

    agent_count = result.samples.get("agent_count", 0.0) or 0.0
    retry_count = result.samples.get("retry_count", 0.0) or 0.0
    agent_avg = (
        (result.samples.get("agent_sum", 0.0) / agent_count) if agent_count else 0.0
    )
    retry_avg = (
        (result.samples.get("retry_sum", 0.0) / retry_count) if retry_count else 0.0
    )

    lines.extend(
        [
            "",
            "## Prometheus Samples",
            "",
            f"- Success counter: {result.samples.get('success_total', 0.0):.0f}",
            f"- Failure counter: {result.samples.get('failure_total', 0.0):.0f}",
            f"- Retry counter: {result.samples.get('retry_total', 0.0):.0f}",
            f"- Average agent latency: {agent_avg:.3f} s",
            f"- Average retry duration: {retry_avg:.3f} s",
            "",
            "## Milestone Alignment",
            "",
            (
                "These burst tolerances underpin the **Root chakra upgrade (Q3 2024)** "
                "milestone"
            ),
            (
                "documented in [ABSOLUTE_MILESTONES.md](../ABSOLUTE_MILESTONES.md), "
                "ensuring"
            ),
            "escalation paths remain stable as memory throughput grows.",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--component", default=DEFAULT_COMPONENT, help="Component label"
    )
    parser.add_argument("--agent", default=DEFAULT_AGENT, help="Agent label")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown file to update with benchmark results",
    )
    parser.add_argument("--seed", type=int, default=1337, help="Random seed")
    parser.add_argument(
        "--enable-server",
        action="store_true",
        help="Expose the Prometheus endpoint instead of stubbing the HTTP server",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    result = run_benchmark(
        component=args.component,
        agent=args.agent,
        seed=args.seed,
        enable_server=args.enable_server,
    )
    write_report(result, args.output)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
