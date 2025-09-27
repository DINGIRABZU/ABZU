"""Fallback implementation for the :mod:`neoabzu_memory` bindings.

The real bundle is a Rust extension. When it is unavailable (for example on
CI workers without the compiled library) the Python entrypoints fall back to
this lightweight shim so higher-level services can continue running. The stub
provides deterministic diagnostics for :meth:`initialize` and mock data for
``query`` calls so latency measurements remain meaningful even in degraded
environments.
"""

from __future__ import annotations

from typing import Any, Dict

from agents.event_bus import emit_event


__all__ = ["MemoryBundle", "STUBBED_LAYERS"]


STUBBED_LAYERS: tuple[str, ...] = (
    "cortex",
    "vector",
    "spiral",
    "emotional",
    "mental",
    "spiritual",
    "narrative",
    "core",
)


class MemoryBundle:
    """Stand-in for the Rust ``neoabzu_memory.MemoryBundle`` class."""

    fallback_reason = "neoabzu_memory_unavailable"
    bundle_mode = "stubbed"

    def __init__(self, import_error: BaseException | None = None) -> None:
        self._import_error = import_error
        self.stubbed = True
        self.bundle_source = "memory.optional.neoabzu_bundle"
        self._initialized = False
        self.statuses: Dict[str, str] = {}
        self.diagnostics: Dict[str, Dict[str, Any]] = {}

    def _build_attempts(self) -> list[Dict[str, Any]]:
        attempts = [
            {
                "module": "neoabzu_memory",
                "outcome": "error",
                "error": (
                    repr(self._import_error)
                    if self._import_error is not None
                    else "module_not_found"
                ),
            },
            {
                "module": "memory.optional.neoabzu_bundle",
                "outcome": "loaded",
            },
        ]
        return attempts

    def initialize(self) -> Dict[str, Any]:
        """Return deterministic statuses and diagnostics for each layer."""

        self.statuses = {layer: "skipped" for layer in STUBBED_LAYERS}
        attempts = self._build_attempts()
        self.diagnostics = {
            layer: {
                "status": "skipped",
                "fallback_reason": self.fallback_reason,
                "loaded_module": "memory.optional.neoabzu_bundle",
                "attempts": [dict(entry) for entry in attempts],
            }
            for layer in STUBBED_LAYERS
        }

        emit_event(
            "memory",
            "layer_init",
            {"layers": {layer: "skipped" for layer in STUBBED_LAYERS}},
        )

        self._initialized = True
        return {
            "statuses": dict(self.statuses),
            "diagnostics": {
                layer: {
                    **info,
                    "attempts": [dict(entry) for entry in info.get("attempts", [])],
                }
                for layer, info in self.diagnostics.items()
            },
            "stubbed": True,
            "fallback_reason": self.fallback_reason,
            "bundle_source": self.bundle_source,
            "bundle_mode": self.bundle_mode,
        }

    def query(self, text: str) -> Dict[str, Any]:
        """Return a predictable payload for latency measurements."""

        if not self._initialized:
            self.initialize()

        response = {
            "cortex": [
                {
                    "text": text,
                    "similarity": 1.0,
                    "source": "stub-cortex",
                }
            ],
            "vector": [
                {
                    "embedding": [0.0, 0.0, 0.0],
                    "score": 0.0,
                    "source": "stub-vector",
                }
            ],
            "spiral": {
                "resonance": 0.0,
                "summary": f"stubbed spiral echo for '{text}'",
            },
            "emotional": [{"affect": "neutral", "confidence": 1.0}],
            "mental": [{"task": "stubbed", "relevance": 0.0}],
            "spiritual": [{"symbol": "stub", "meaning": "placeholder"}],
            "narrative": [{"story": "stub narrative", "coherence": 1.0}],
            "core": "stub-eval",
            "failed_layers": [],
            "stubbed": True,
        }
        return response
