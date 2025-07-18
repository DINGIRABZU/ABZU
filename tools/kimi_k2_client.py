from __future__ import annotations

"""HTTP client for the Kimi-K2 servant model."""

import logging
import os

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - when requests missing
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

_ENDPOINT = os.getenv("KIMI_K2_URL", "http://localhost:8004")


def complete(prompt: str) -> str:
    """Return the completion from Kimi-K2 for ``prompt``."""
    if requests is None:
        logger.warning("requests missing; returning empty response")
        return ""

    try:
        resp = requests.post(_ENDPOINT, json={"prompt": prompt}, timeout=10)
        resp.raise_for_status()
        try:
            return resp.json().get("text", "")
        except Exception:
            return resp.text
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("Kimi-K2 request failed: %s", exc)
        return ""


__all__ = ["complete"]
