"""Health check routines for Razar boot components."""

from __future__ import annotations

import json
import logging
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List

LOGGER = logging.getLogger("razar.health_checks")


def ready_signal(url: str, timeout: int = 5, retries: int = 3, interval: float = 1.0) -> bool:
    """Return ``True`` if ``url`` reports a ready status."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                url, timeout=timeout
            ) as resp:  # nosec B310 - trusted endpoints
                if not 200 <= resp.status < 300:
                    raise RuntimeError(f"status {resp.status}")
                data = resp.read()
            payload = json.loads(data)
            return payload.get("status") == "ready"
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.error("Ready check failed for %s (attempt %s/%s): %s", url, attempt + 1, retries, exc)
            time.sleep(interval)
    return False


def ping_endpoint(url: str, timeout: int = 5, retries: int = 3, interval: float = 1.0) -> bool:
    """Return ``True`` if ``url`` responds within ``timeout`` seconds."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                url, timeout=timeout
            ) as resp:  # nosec B310 - trusted endpoints
                if 200 <= resp.status < 300:
                    return True
                raise RuntimeError(f"status {resp.status}")
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.error(
                "Ping failed for %s (attempt %s/%s): %s", url, attempt + 1, retries, exc
            )
            time.sleep(interval)
    return False


def verify_log(path: Path, phrase: str) -> bool:
    """Return ``True`` if ``phrase`` is found in ``path``."""
    try:
        data = Path(path).read_text()
    except OSError as exc:  # pragma: no cover - filesystem dependent
        LOGGER.error("Could not read log %s: %s", path, exc)
        return False
    return phrase in data


def check_basic_service() -> bool:
    """Example check for ``basic_service``."""
    return ping_endpoint("http://localhost:8000/healthz")


def check_complex_service() -> bool:
    """Example check for ``complex_service``."""
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
    """Run health check for ``name`` and return ``True`` on success.

    If the initial check fails and a restart command is registered, attempt to
    restart the component once before reporting failure.
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
