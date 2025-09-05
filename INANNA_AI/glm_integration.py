"""Wrapper around a placeholder GLM-4.1V-9B endpoint."""

from __future__ import annotations

import asyncio
import logging
import os

try:  # pragma: no cover - optional dependency
    import aiohttp
except Exception:  # pragma: no cover - fallback when aiohttp missing
    aiohttp = None  # type: ignore

try:  # pragma: no cover - enforce dependency
    import requests
except ImportError as exc:  # pragma: no cover - requests must be installed
    raise ImportError(
        "GLMIntegration requires the 'requests' package."
        " Install it via 'pip install requests'."
    ) from exc

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://glm.example.com/glm41v_9b"
SAFE_ERROR_MESSAGE = "GLM unavailable"


class GLMIntegration:
    """Small wrapper around a GLM endpoint."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.8,
    ) -> None:
        """Initialize from arguments or environment variables."""
        if endpoint is None:
            endpoint = os.getenv("GLM_API_URL", DEFAULT_ENDPOINT)
        if api_key is None:
            api_key = os.getenv("GLM_API_KEY")
        self.endpoint = endpoint
        self.api_key = api_key
        self.temperature = temperature

        # Fail fast if the GLM endpoint cannot be reached at startup.
        self.health_check()

    @property
    def headers(self) -> dict[str, str] | None:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return None

    def complete(self, prompt: str, *, quantum_context: str | None = None) -> str:
        """Return the GLM completion for ``prompt``.

        ``quantum_context`` is included in the request payload when provided.
        """
        payload = {"prompt": prompt, "temperature": self.temperature}
        if quantum_context is not None:
            payload["quantum_context"] = quantum_context
        try:
            resp = requests.post(
                self.endpoint, json=payload, timeout=10, headers=self.headers
            )
            resp.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            logger.error("Failed to query %s: %s", self.endpoint, exc)
            raise RuntimeError(f"GLM request failed: {exc}") from exc

        try:
            text = resp.json().get("text", "")
        except Exception:  # pragma: no cover - non-json response
            text = resp.text
        return text

    async def complete_async(
        self, prompt: str, *, quantum_context: str | None = None
    ) -> str:
        """Asynchronously return the GLM completion for ``prompt``.

        Uses :mod:`aiohttp` when available and falls back to running
        :meth:`complete` in a thread when it isn't.
        """
        if aiohttp is None:
            logger.warning("aiohttp missing; using thread fallback")
            return await asyncio.to_thread(
                self.complete, prompt, quantum_context=quantum_context
            )

        payload = {"prompt": prompt, "temperature": self.temperature}
        if quantum_context is not None:
            payload["quantum_context"] = quantum_context
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(
                    self.endpoint, json=payload, timeout=10
                ) as resp:
                    resp.raise_for_status()
                    try:
                        data = await resp.json()
                        text = data.get("text", "")
                    except Exception:  # pragma: no cover - non-json response
                        text = await resp.text()
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Failed to query %s: %s", self.endpoint, exc)
            raise RuntimeError(f"GLM async request failed: {exc}") from exc
        return text

    def health_check(self) -> None:
        """Validate connectivity to the GLM endpoint."""
        url = self.endpoint.rstrip("/") + "/health"
        try:
            resp = requests.get(url, timeout=5, headers=self.headers)
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors
            raise RuntimeError(f"GLM health check failed: {exc}") from exc


__all__ = ["GLMIntegration", "DEFAULT_ENDPOINT", "SAFE_ERROR_MESSAGE"]
