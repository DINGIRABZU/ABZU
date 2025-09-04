"""Client for interacting with the Opencode servant model."""

from __future__ import annotations

__version__ = "0.1.0"

import logging
import os
import subprocess

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - requests optional
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

_ENDPOINT = os.getenv("OPENCODE_URL")


def complete(prompt: str) -> str:
    """Return the code diff for ``prompt`` via Opencode.

    If ``OPENCODE_URL`` is set, an HTTP request is issued. Otherwise the local
    ``opencode`` CLI is invoked. Errors are wrapped in :class:`RuntimeError`.
    """

    try:
        if _ENDPOINT and requests is not None:
            resp = requests.post(_ENDPOINT, json={"prompt": prompt}, timeout=30)
            resp.raise_for_status()
            try:
                data = resp.json()
                return data.get("diff", data.get("text", ""))
            except Exception:
                return resp.text
        cmd = ["opencode", "--diff"]
        proc = subprocess.run(
            cmd,
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=30,
        )
        return proc.stdout.decode().strip()
    except Exception as exc:  # pragma: no cover - external failures
        logger.error("Opencode request failed: %s", exc)
        raise RuntimeError("Opencode request failed") from exc


__all__ = ["complete"]
