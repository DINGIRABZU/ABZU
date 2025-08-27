from __future__ import annotations

"""Health check routines for RAZAR runtime components.

This module defines simple probe functions and a ``run`` helper that executes
checks for named services.  Each check returns ``True`` on success.  If a check
fails and a restart command is configured the component is restarted once before
reporting failure.
"""

import json
import logging
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List

LOGGER = logging.getLogger("agents.razar.health_checks")


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
    """Confirm Inanna AI reports readiness."""
    return ready_signal("http://localhost:8000/ready")


def check_crown_ready() -> bool:
    """Confirm CROWN LLM reports readiness."""
    return ready_signal("http://localhost:8001/ready")


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
    if func():
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
    return func()
