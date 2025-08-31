from __future__ import annotations

"""Minimal connector for sending metrics to the Primordials service.

This module posts JSON payloads to the Primordials API. It is intentionally
lightweight and relies only on the standard library to avoid additional
runtime dependencies.
"""

__version__ = "0.1.1"

import json
import logging
import os
import urllib.request
from typing import Any, Mapping


logger = logging.getLogger(__name__)

_PRIMORDIALS_URL = os.getenv("PRIMORDIALS_API_URL", "http://localhost:8000")


def send_metrics(metrics: Mapping[str, Any]) -> bool:
    """POST ``metrics`` to the Primordials service.

    Parameters
    ----------
    metrics:
        Mapping of metric names to values.
    """

    url = f"{_PRIMORDIALS_URL}/metrics"
    data = json.dumps(metrics).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5):  # pragma: no cover - network
            return True
    except Exception as exc:  # pragma: no cover - network
        logger.warning("failed to send metrics: %s", exc)
        return False


def check_health() -> bool:
    """Return ``True`` if the Primordials service responds to ``/health``."""

    url = f"{_PRIMORDIALS_URL}/health"
    try:
        with urllib.request.urlopen(
            url, timeout=5
        ) as resp:  # pragma: no cover - network
            return resp.status == 200
    except Exception as exc:  # pragma: no cover - network
        logger.warning("primordials health check failed: %s", exc)
        return False


__all__ = ["send_metrics", "check_health"]
