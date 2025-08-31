from __future__ import annotations

"""Minimal connector for sending metrics to the Primordials service.

This module posts JSON payloads to the Primordials API. It is intentionally
lightweight and relies only on the standard library to avoid additional
runtime dependencies.
"""

__version__ = "0.1.0"

import json
import os
import urllib.request
from typing import Mapping, Any


_PRIMORDIALS_URL = os.getenv("PRIMORDIALS_API_URL", "http://localhost:8000")


def send_metrics(metrics: Mapping[str, Any]) -> None:
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
            pass
    except Exception:
        # Best-effort; failures are logged silently to avoid raising in calling code.
        return


__all__ = ["send_metrics"]
