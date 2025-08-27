from __future__ import annotations

"""Health check routines for RAZAR runtime components.

This module defines probe functions for runtime services and a ``run`` helper
that executes checks for named services.  Each check returns ``True`` on
success.  If a check fails and a restart command is configured the component is
restarted once before reporting failure.  Health status and latency metrics are
exported via Prometheus when the ``prometheus_client`` package is available.
"""

import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List

try:  # pragma: no cover - optional dependency
    from prometheus_client import Gauge, start_http_server
except Exception:  # pragma: no cover - optional dependency
    Gauge = start_http_server = None  # type: ignore

LOGGER = logging.getLogger("agents.razar.health_checks")

HEALTH_GAUGE: Gauge | None = None
LATENCY_GAUGE: Gauge | None = None


def init_metrics(port: int = 9350) -> None:
    """Start a Prometheus server if the client library is installed."""

    global HEALTH_GAUGE, LATENCY_GAUGE
    if Gauge is None or start_http_server is None or HEALTH_GAUGE is not None:
        return
    HEALTH_GAUGE = Gauge("service_health_status", "1=healthy,0=unhealthy", ["service"])
    LATENCY_GAUGE = Gauge(
        "service_health_latency_seconds",
        "Health check latency in seconds",
        ["service"],
    )
    start_http_server(port)
    LOGGER.info("Prometheus metrics exposed on port %s", port)


def ready_signal(url: str, timeout: int = 5) -> bool:
    """Return ``True`` if ``url`` reports a ready status."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310
            if not 200 <= resp.status < 300:
                return False
            data = resp.read()
        payload = json.loads(data)
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.error("Ready check failed for %s: %s", url, exc)
        return False
    return payload.get("status") == "ready"


def ping_endpoint(url: str, timeout: int = 5) -> bool:
    """Return ``True`` if ``url`` responds within ``timeout`` seconds."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310
            return 200 <= resp.status < 300
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.error("Ping failed for %s: %s", url, exc)
        return False


def verify_log(path: Path, phrase: str) -> bool:
    """Return ``True`` if ``phrase`` is found in ``path``."""
    try:
        data = Path(path).read_text()
    except OSError as exc:  # pragma: no cover - filesystem dependent
        LOGGER.error("Could not read log %s: %s", path, exc)
        return False
    return phrase in data


# ---------------------------------------------------------------------------
# Example service-specific probes
# ---------------------------------------------------------------------------


def check_basic_service() -> bool:
    """Example check for a basic HTTP service."""
    return ping_endpoint("http://localhost:8000/healthz")


def check_complex_service() -> bool:
    """Example check for a service that writes a start-up log entry."""
    return verify_log(Path("/var/log/complex_service.log"), "started")


def check_inanna_ready() -> bool:
    """Confirm Inanna AI reports readiness.

    The service port can be overridden with the ``INANNA_PORT`` environment
    variable to support custom deployments.
    """

    port = os.getenv("INANNA_PORT", "8000")
    return ready_signal(f"http://localhost:{port}/ready")


def check_crown_ready() -> bool:
    """Confirm CROWN LLM reports readiness.

    ``CROWN_PORT`` may override the default port of ``8001``.
    """

    port = os.getenv("CROWN_PORT", "8001")
    return ready_signal(f"http://localhost:{port}/ready")


CHECKS: Dict[str, Callable[[], bool]] = {
    "basic_service": check_basic_service,
    "complex_service": check_complex_service,
    "inanna_ai": check_inanna_ready,
    "crown_llm": check_crown_ready,
}


RESTART_COMMANDS: Dict[str, List[str]] = {
    "inanna_ai": ["bash", "run_inanna.sh"],
    "crown_llm": ["bash", "crown_model_launcher.sh"],
}


# Maximum allowed latency in seconds for each check
THRESHOLDS: Dict[str, float] = {
    "basic_service": 0.5,
    "complex_service": 0.5,
    "inanna_ai": 1.0,
    "crown_llm": 1.0,
}


def _execute(func: Callable[[], bool], name: str) -> bool:
    """Execute ``func`` and record Prometheus metrics."""

    init_metrics()
    start = time.perf_counter()
    result = func()
    duration = time.perf_counter() - start
    threshold = THRESHOLDS.get(name)
    if result and threshold is not None and duration > threshold:
        LOGGER.warning(
            "Health check for %s exceeded latency %.3fs > %.3fs",
            name,
            duration,
            threshold,
        )
        result = False
    if HEALTH_GAUGE is not None:
        HEALTH_GAUGE.labels(name).set(1 if result else 0)  # type: ignore[call-arg]
        LATENCY_GAUGE.labels(name).set(duration)  # type: ignore[call-arg]
    return result


def run(name: str) -> bool:
    """Run the health check registered for ``name``.

    ``True`` is returned when the component is healthy.  If the check fails and a
    restart command is available the command is executed once and the check is
    repeated.
    """

    func = CHECKS.get(name)
    if not func:
        LOGGER.info("No health check defined for %s", name)
        return True
    if _execute(func, name):
        return True
    LOGGER.warning("Health check failed for %s", name)
    cmd = RESTART_COMMANDS.get(name)
    if not cmd:
        return False
    try:
        subprocess.run(cmd, check=True)
    except Exception as exc:  # pragma: no cover - system dependent
        LOGGER.error("Restart command failed for %s: %s", name, exc)
        return False
    return _execute(func, name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run health checks and expose Prometheus metrics"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Seconds between check cycles",
    )
    args = parser.parse_args()

    while True:
        for service in CHECKS:
            run(service)
        time.sleep(args.interval)
