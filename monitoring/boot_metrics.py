"""Helpers for exporting boot metrics to Prometheus textfiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
    "export_metrics",
]


@dataclass(frozen=True)
class BootMetricNames:
    """Canonical metric names for boot exporters and tests."""

    first_attempt_success: str = "razar_boot_first_attempt_success_total"
    retry_total: str = "razar_boot_retry_total"
    total_time: str = "razar_boot_total_time_seconds"


METRIC_NAMES = BootMetricNames()

BOOT_METRICS_PATH = Path(__file__).resolve().parent / "boot_metrics.prom"

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
else:  # pragma: no cover - metrics disabled without prometheus_client
    BOOT_METRICS_REGISTRY = None  # type: ignore[assignment]
    FIRST_ATTEMPT_SUCCESS_GAUGE = None  # type: ignore[assignment]
    RETRY_TOTAL_GAUGE = None  # type: ignore[assignment]
    TOTAL_TIME_GAUGE = None  # type: ignore[assignment]


@dataclass(frozen=True)
class BootMetricValues:
    """Container for metric values prior to export."""

    first_attempt_success: float
    retry_total: float
    total_time: float


def export_metrics(
    values: BootMetricValues, *, output_path: Optional[Path] = None
) -> Optional[Path]:
    """Write ``values`` to the Prometheus textfile registry."""

    registry = BOOT_METRICS_REGISTRY
    gauge_first = FIRST_ATTEMPT_SUCCESS_GAUGE
    gauge_retry = RETRY_TOTAL_GAUGE
    gauge_time = TOTAL_TIME_GAUGE
    writer = write_to_textfile

    if (
        registry is None
        or gauge_first is None
        or gauge_retry is None
        or gauge_time is None
    ):
        return None

    gauge_first.set(values.first_attempt_success)
    gauge_retry.set(values.retry_total)
    gauge_time.set(values.total_time)

    path = Path(output_path) if output_path is not None else BOOT_METRICS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if writer is not None:
        writer(str(path), registry)
        return path
    return None
