"""Compatibility wrapper exposing :class:`~INANNA_AI.glm_integration.GLMIntegration`.

``GLMIntegration.complete`` accepts an optional ``quantum_context`` string
forwarded to the HTTP payload.
"""

from __future__ import annotations

from ...glm_integration import DEFAULT_ENDPOINT, SAFE_ERROR_MESSAGE, GLMIntegration

__all__ = ["GLMIntegration", "DEFAULT_ENDPOINT", "SAFE_ERROR_MESSAGE"]
