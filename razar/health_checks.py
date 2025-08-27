from __future__ import annotations

"""Health check routines for Razar boot components."""

import logging
import urllib.request
from pathlib import Path
from typing import Callable, Dict

LOGGER = logging.getLogger("razar.health_checks")


def ping_endpoint(url: str, timeout: int = 5) -> bool:
    """Return ``True`` if ``url`` responds within ``timeout`` seconds."""
    try:
        with urllib.request.urlopen(
            url, timeout=timeout
        ) as resp:  # nosec B310 - trusted endpoints
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


def check_basic_service() -> bool:
    """Example check for ``basic_service``."""
    return ping_endpoint("http://localhost:8000/healthz")


def check_complex_service() -> bool:
    """Example check for ``complex_service``."""
    return verify_log(Path("/var/log/complex_service.log"), "started")


CHECKS: Dict[str, Callable[[], bool]] = {
    "basic_service": check_basic_service,
    "complex_service": check_complex_service,
}


def run(name: str) -> bool:
    """Run health check for ``name`` and return ``True`` on success."""
    func = CHECKS.get(name)
    if not func:
        LOGGER.info("No health check defined for %s", name)
        return True
    return func()
