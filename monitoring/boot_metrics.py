"""Helpers for exporting boot metrics to Prometheus textfiles."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

try:  # pragma: no cover - optional dependency
    from prometheus_client import CollectorRegistry, Gauge, write_to_textfile
except Exception:  # pragma: no cover - optional dependency
    CollectorRegistry = None  # type: ignore[assignment]
    Gauge = None  # type: ignore[assignment]
    write_to_textfile = None  # type: ignore[assignment]

__all__ = [
    "BootMetricNames",
    "METRIC_NAMES",
    "BOOT_METRICS_PATH",
    "BOOT_METRICS_REGISTRY",
    "FIRST_ATTEMPT_SUCCESS_GAUGE",
    "RETRY_TOTAL_GAUGE",
    "TOTAL_TIME_GAUGE",
    "BootMetricValues",
    "SUCCESS_RATE_GAUGE",
    "COMPONENT_TOTAL_GAUGE",
    "COMPONENT_SUCCESS_GAUGE",
    "COMPONENT_FAILURE_GAUGE",
    "export_metrics",
    "MemoryInitMetricNames",
    "MEMORY_INIT_METRIC_NAMES",
    "MemoryInitMetricValues",
    "record_memory_init_metrics",
    "summarize_memory_statuses",
]


@dataclass(frozen=True)
class BootMetricNames:
    """Canonical metric names for boot exporters and tests."""

    first_attempt_success: str = "razar_boot_first_attempt_success_total"
    retry_total: str = "razar_boot_retry_total"
    total_time: str = "razar_boot_total_time_seconds"
    success_rate: str = "razar_boot_success_rate"
    component_total: str = "razar_boot_component_total"
    component_success_total: str = "razar_boot_component_success_total"
    component_failure_total: str = "razar_boot_component_failure_total"


METRIC_NAMES = BootMetricNames()

BOOT_METRICS_PATH = Path(__file__).resolve().parent / "boot_metrics.prom"


@dataclass(frozen=True)
class MemoryInitMetricNames:
    """Canonical metric names for memory initialization telemetry."""

    duration: str = "razar_memory_init_duration_seconds"
    layer_total: str = "razar_memory_init_layer_total"
    layer_ready: str = "razar_memory_init_layer_ready_total"
    layer_failed: str = "razar_memory_init_layer_failed_total"
    error: str = "razar_memory_init_error"
    invocations: str = "razar_memory_init_invocations_total"


MEMORY_INIT_METRIC_NAMES = MemoryInitMetricNames()

if CollectorRegistry is not None and Gauge is not None:  # pragma: no branch
    BOOT_METRICS_REGISTRY = CollectorRegistry()
    FIRST_ATTEMPT_SUCCESS_GAUGE = Gauge(
        METRIC_NAMES.first_attempt_success,
        "First-attempt successes recorded during the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    RETRY_TOTAL_GAUGE = Gauge(
        METRIC_NAMES.retry_total,
        "Total retries performed across all components in the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    TOTAL_TIME_GAUGE = Gauge(
        METRIC_NAMES.total_time,
        "Wall-clock time required to finish the latest boot sequence in seconds.",
        registry=BOOT_METRICS_REGISTRY,
    )
    SUCCESS_RATE_GAUGE = Gauge(
        METRIC_NAMES.success_rate,
        "Overall success ratio recorded during the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    COMPONENT_TOTAL_GAUGE = Gauge(
        METRIC_NAMES.component_total,
        "Total components evaluated during the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    COMPONENT_SUCCESS_GAUGE = Gauge(
        METRIC_NAMES.component_success_total,
        "Components that completed successfully in the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    COMPONENT_FAILURE_GAUGE = Gauge(
        METRIC_NAMES.component_failure_total,
        "Components that failed in the latest boot run.",
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_DURATION_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.duration,
        "Duration of MemoryBundle.initialize grouped by source in seconds.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_LAYER_TOTAL_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.layer_total,
        "Total memory layers observed during initialization by source.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_LAYER_READY_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.layer_ready,
        "Memory layers reporting ready status during initialization.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_LAYER_FAILED_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.layer_failed,
        "Memory layers reporting failure status during initialization.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_ERROR_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.error,
        "Flag indicating whether initialization surfaced errors or failures.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
    MEMORY_INIT_INVOCATIONS_GAUGE = Gauge(
        MEMORY_INIT_METRIC_NAMES.invocations,
        "Cumulative MemoryBundle.initialize invocations grouped by source.",
        ["source"],
        registry=BOOT_METRICS_REGISTRY,
    )
else:  # pragma: no cover - metrics disabled without prometheus_client
    BOOT_METRICS_REGISTRY = None  # type: ignore[assignment]
    FIRST_ATTEMPT_SUCCESS_GAUGE = None  # type: ignore[assignment]
    RETRY_TOTAL_GAUGE = None  # type: ignore[assignment]
    TOTAL_TIME_GAUGE = None  # type: ignore[assignment]
    SUCCESS_RATE_GAUGE = None  # type: ignore[assignment]
    COMPONENT_TOTAL_GAUGE = None  # type: ignore[assignment]
    COMPONENT_SUCCESS_GAUGE = None  # type: ignore[assignment]
    COMPONENT_FAILURE_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_DURATION_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_LAYER_TOTAL_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_LAYER_READY_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_LAYER_FAILED_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_ERROR_GAUGE = None  # type: ignore[assignment]
    MEMORY_INIT_INVOCATIONS_GAUGE = None  # type: ignore[assignment]


@dataclass(frozen=True)
class BootMetricValues:
    """Container for metric values prior to export."""

    first_attempt_success: float
    retry_total: float
    total_time: float
    success_rate: float
    component_total: float
    component_success: float
    component_failure: float


@dataclass(frozen=True)
class MemoryInitMetricValues:
    """Container for memory initialization metric values."""

    duration_seconds: float
    layer_total: float
    layer_ready: float
    layer_failed: float
    source: str
    error: bool = False


_MEMORY_INIT_INVOCATION_COUNTS: Counter[str] = Counter()


def export_metrics(
    values: BootMetricValues, *, output_path: Optional[Path] = None
) -> Optional[Path]:
    """Write ``values`` to the Prometheus textfile registry."""

    registry = BOOT_METRICS_REGISTRY
    gauge_first = FIRST_ATTEMPT_SUCCESS_GAUGE
    gauge_retry = RETRY_TOTAL_GAUGE
    gauge_time = TOTAL_TIME_GAUGE
    gauge_success_rate = SUCCESS_RATE_GAUGE
    gauge_component_total = COMPONENT_TOTAL_GAUGE
    gauge_component_success = COMPONENT_SUCCESS_GAUGE
    gauge_component_failure = COMPONENT_FAILURE_GAUGE
    writer = write_to_textfile

    if (
        registry is None
        or gauge_first is None
        or gauge_retry is None
        or gauge_time is None
        or gauge_success_rate is None
        or gauge_component_total is None
        or gauge_component_success is None
        or gauge_component_failure is None
    ):
        return None

    gauge_first.set(values.first_attempt_success)
    gauge_retry.set(values.retry_total)
    gauge_time.set(values.total_time)
    gauge_success_rate.set(values.success_rate)
    gauge_component_total.set(values.component_total)
    gauge_component_success.set(values.component_success)
    gauge_component_failure.set(values.component_failure)

    path = Path(output_path) if output_path is not None else BOOT_METRICS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if writer is not None:
        writer(str(path), registry)
        return path
    return None


def record_memory_init_metrics(
    values: MemoryInitMetricValues, *, output_path: Optional[Path] = None
) -> Optional[Path]:
    """Write memory initialization metrics to the Prometheus textfile registry."""

    registry = BOOT_METRICS_REGISTRY
    gauge_duration = MEMORY_INIT_DURATION_GAUGE
    gauge_total = MEMORY_INIT_LAYER_TOTAL_GAUGE
    gauge_ready = MEMORY_INIT_LAYER_READY_GAUGE
    gauge_failed = MEMORY_INIT_LAYER_FAILED_GAUGE
    gauge_error = MEMORY_INIT_ERROR_GAUGE
    gauge_invocations = MEMORY_INIT_INVOCATIONS_GAUGE
    writer = write_to_textfile

    source_label = values.source or "unknown"
    _MEMORY_INIT_INVOCATION_COUNTS[source_label] += 1

    if (
        registry is None
        or gauge_duration is None
        or gauge_total is None
        or gauge_ready is None
        or gauge_failed is None
        or gauge_error is None
        or gauge_invocations is None
    ):
        return None

    labels = {"source": source_label}
    gauge_duration.labels(**labels).set(values.duration_seconds)
    gauge_total.labels(**labels).set(values.layer_total)
    gauge_ready.labels(**labels).set(values.layer_ready)
    gauge_failed.labels(**labels).set(values.layer_failed)
    gauge_error.labels(**labels).set(1.0 if values.error else 0.0)
    gauge_invocations.labels(**labels).set(
        float(_MEMORY_INIT_INVOCATION_COUNTS[source_label])
    )

    path = Path(output_path) if output_path is not None else BOOT_METRICS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if writer is not None:
        writer(str(path), registry)
        return path
    return None


_SUCCESS_TOKENS = (
    "ready",
    "ok",
    "success",
    "available",
    "active",
    "initialized",
    "healthy",
    "complete",
)
_FAILURE_TOKENS = (
    "fail",
    "error",
    "missing",
    "timeout",
    "panic",
    "unavailable",
    "blocked",
    "skipped",
)


def summarize_memory_statuses(statuses: Mapping[str, object]) -> tuple[int, int, int]:
    """Return ``(total, ready, failed)`` counts for memory layer ``statuses``."""

    total = len(statuses)
    ready = 0
    for status in statuses.values():
        text = str(status).strip().lower()
        if not text:
            continue
        if any(token in text for token in _FAILURE_TOKENS):
            continue
        if any(token in text for token in _SUCCESS_TOKENS):
            ready += 1
            continue
        # Treat neutral statuses as failures to avoid masking issues.
    failed = total - ready
    return total, ready, failed
