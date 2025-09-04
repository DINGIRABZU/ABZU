"""HTTP client for the Kimi-K2 servant model."""

from __future__ import annotations

__version__ = "0.1.0"

import logging
import os

try:  # pragma: no cover - enforce dependency
    import requests
except ImportError as exc:  # pragma: no cover - requests must be installed
    raise ImportError(
        "Kimi-K2 client requires the 'requests' package."
        " Install it via 'pip install requests'."
    ) from exc

logger = logging.getLogger(__name__)

_ENDPOINT = os.getenv("KIMI_K2_URL", "http://localhost:8004")


def endpoint() -> str:
    """Return the configured Kimi-K2 endpoint."""

    return _ENDPOINT


def complete(prompt: str) -> str:
    """Return the completion from Kimi-K2 for ``prompt``."""

    try:
        resp = requests.post(_ENDPOINT, json={"prompt": prompt}, timeout=10)
        resp.raise_for_status()
        try:
            return resp.json().get("text", "")
        except Exception:
            return resp.text
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("Kimi-K2 request failed: %s", exc)
        raise RuntimeError("Kimi-K2 request failed") from exc


__all__ = ["complete", "endpoint"]
