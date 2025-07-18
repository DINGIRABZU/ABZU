from __future__ import annotations

"""Wrapper around a placeholder GLM-4.1V-9B endpoint."""

import logging
import os

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - fallback when requests missing
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "https://api.example.com/glm41v_9b"
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

    @property
    def headers(self) -> dict[str, str] | None:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return None

    def complete(self, prompt: str, *, quantum_context: str | None = None) -> str:
        """Return the GLM completion for ``prompt``.

        ``quantum_context`` is included in the request payload when provided.
        """
        if requests is None:
            logger.warning("requests missing; returning safe message")
            return SAFE_ERROR_MESSAGE

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
            return SAFE_ERROR_MESSAGE

        try:
            text = resp.json().get("text", "")
        except Exception:  # pragma: no cover - non-json response
            text = resp.text
        return text or SAFE_ERROR_MESSAGE


__all__ = ["GLMIntegration", "DEFAULT_ENDPOINT", "SAFE_ERROR_MESSAGE"]
