from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import psutil

from os_guardian import action_engine

try:  # pragma: no cover - optional dependency
    from prometheus_client import CollectorRegistry, Gauge, start_http_server
except Exception:  # pragma: no cover - optional dependency
    CollectorRegistry = Gauge = start_http_server = None  # type: ignore

ALERT_DIR = Path(__file__).with_name("alerts")
ALERT_DIR.mkdir(exist_ok=True)

LOGGER = logging.getLogger(__name__)

CPU_THRESHOLD = 90.0
MEM_THRESHOLD_MB = 1024
FD_THRESHOLD = 1024
CHECK_INTERVAL = 5.0
PROM_PORT = 9100

SERVICES: Dict[str, Dict[str, Any]] = {
    # "service-name": {
    #     "match": "process-name-or-path",
    #     "restart": ["systemctl", "restart", "service-name"],
    # },
}


def find_process(match: str) -> psutil.Process | None:
    """Locate the first process whose name or cmdline contains ``match``."""
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = proc.info.get("name") or ""
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if match in name or match in cmdline:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def emit_alert(service: str, metric: str, value: Any, threshold: Any) -> None:
    """Emit an alert to stdout and a JSON file, then attempt restart."""
    data = {
        "service": service,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    print(json.dumps(data))
    path = ALERT_DIR / f"{service}_{int(time.time())}.json"
    path.write_text(json.dumps(data))

    restart = SERVICES.get(service, {}).get("restart")
    if restart:
        action_engine.run_command(restart)


def monitor() -> None:
    """Monitor configured services for resource usage."""
    registry = cpu_gauge = mem_gauge = fd_gauge = None
    if start_http_server is not None:
        registry = CollectorRegistry()  # type: ignore[assignment]
        cpu_gauge = Gauge(
            "service_cpu_percent", "CPU percent", ["service"], registry=registry
        )  # type: ignore[assignment]
        mem_gauge = Gauge(
            "service_memory_mb", "Memory RSS in MB", ["service"], registry=registry
        )  # type: ignore[assignment]
        fd_gauge = Gauge(
            "service_open_fds", "Open file descriptors", ["service"], registry=registry
        )  # type: ignore[assignment]
        start_http_server(PROM_PORT, registry=registry)  # type: ignore[arg-type]
        LOGGER.info("Prometheus metrics exposed on port %s", PROM_PORT)

    while True:
        for name, cfg in SERVICES.items():
            proc = find_process(str(cfg.get("match", name)))
            if proc is None:
                emit_alert(name, "status", "not found", "running")
                continue
            with proc.oneshot():
                cpu = proc.cpu_percent(interval=None)
                mem = proc.memory_info().rss / (1024 * 1024)
                fds = (
                    proc.num_fds() if hasattr(proc, "num_fds") else len(proc.open_files())
                )

            if cpu_gauge is not None:
                cpu_gauge.labels(name).set(cpu)  # type: ignore[call-arg]
                mem_gauge.labels(name).set(mem)  # type: ignore[call-arg]
                fd_gauge.labels(name).set(fds)  # type: ignore[call-arg]

            if cpu > CPU_THRESHOLD:
                emit_alert(name, "cpu", cpu, CPU_THRESHOLD)
            if mem > MEM_THRESHOLD_MB:
                emit_alert(name, "memory", mem, MEM_THRESHOLD_MB)
            if fds > FD_THRESHOLD:
                emit_alert(name, "fds", fds, FD_THRESHOLD)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    monitor()
