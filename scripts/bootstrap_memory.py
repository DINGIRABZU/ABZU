#!/usr/bin/env python3
"""Initialize all memory layers and report readiness."""
from __future__ import annotations

import logging

import time
from typing import Optional

from memory.bundle import MemoryBundle
from monitoring.boot_metrics import (
    MemoryInitMetricValues,
    record_memory_init_metrics,
    summarize_memory_statuses,
)

__version__ = "0.2.0"

LOGGER = logging.getLogger("scripts.bootstrap_memory")


def _initialize_with_metrics(bundle: MemoryBundle) -> dict[str, str]:
    """Initialize the bundle while capturing telemetry and metrics."""

    start = time.perf_counter()
    statuses: dict[str, str] = {}
    error: Optional[BaseException] = None
    try:
        statuses = bundle.initialize()
        return statuses
    except Exception as exc:  # pragma: no cover - delegate to caller
        error = exc
        raise
    finally:
        duration = time.perf_counter() - start
        total, ready, failed = summarize_memory_statuses(statuses)
        log_extra = {
            "memory_init_duration": duration,
            "memory_init_failed": failed,
            "memory_init_ready": ready,
            "memory_layers": statuses,
            "memory_init_source": "bootstrap_memory",
        }
        if error is not None:
            LOGGER.error(
                "Memory bundle initialization failed after %.3fs",
                duration,
                exc_info=error,
                extra=log_extra,
            )
        else:
            LOGGER.info(
                "Memory bundle initialization finished in %.3fs "
                "(%s/%s ready, %s failed)",
                duration,
                ready,
                total,
                failed,
                extra=log_extra,
            )
        try:
            record_memory_init_metrics(
                MemoryInitMetricValues(
                    duration_seconds=float(duration),
                    layer_total=float(total),
                    layer_ready=float(ready),
                    layer_failed=float(failed),
                    source="bootstrap_memory",
                    error=(error is not None) or failed > 0,
                )
            )
        except Exception:  # pragma: no cover - best-effort metrics export
            LOGGER.debug(
                "Unable to export memory initialization metrics", exc_info=True
            )


def main() -> None:
    """Bootstrap memory layers and log their status."""
    logging.basicConfig(level=logging.INFO)
    bundle = MemoryBundle()
    statuses = _initialize_with_metrics(bundle)
    for layer, status in statuses.items():
        logging.info("%s: %s", layer, status)


if __name__ == "__main__":
    main()
