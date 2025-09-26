# Patent pending – see PATENTS.md
"""Thin wrapper around the Rust memory bundle."""

from __future__ import annotations

import logging
from typing import Any, Dict

try:
    from neoabzu_memory import MemoryBundle as _NeoBundle  # type: ignore

    def _bundle_factory() -> Any:
        return _NeoBundle()

    _BUNDLE_SOURCE = "neoabzu_memory"
    _IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as exc:
    from memory.optional.neoabzu_stub import MemoryBundle as _StubBundle

    _BUNDLE_SOURCE = "memory.optional.neoabzu_stub"
    _IMPORT_ERROR = exc

    def _bundle_factory() -> Any:
        return _StubBundle(import_error=_IMPORT_ERROR)


from memory.tracing import get_tracer

__version__ = "0.2.0"


logger = logging.getLogger("memory.bundle")


class MemoryBundle:
    """Proxy class delegating to the Rust implementation."""

    def __init__(self) -> None:
        self._bundle = _bundle_factory()
        self._tracer = get_tracer(__name__)
        self.stubbed: bool = getattr(self._bundle, "stubbed", False)
        self.implementation: str | None = getattr(
            self._bundle, "implementation", _BUNDLE_SOURCE
        )
        self.fallback_reason: str | None = getattr(
            self._bundle, "fallback_reason", None
        )
        if _IMPORT_ERROR is not None:
            logger.warning(
                "neoabzu_memory unavailable – using stub bundle",
                extra={
                    "bundle_source": _BUNDLE_SOURCE,
                    "error": repr(_IMPORT_ERROR),
                },
            )
        self.statuses: Dict[str, str] = {}
        self.diagnostics: Dict[str, Any] = {}

    def initialize(self) -> Dict[str, str]:
        """Initialize memory layers through the Rust bundle.

        Returns
        -------
        Dict[str, str]
            Mapping of layer names to their initialization status. Detailed
            diagnostic metadata emitted by the Rust extension (including import
            attempts, fallback selections, and failure reasons) is stored on
            :attr:`diagnostics` for callers that need richer introspection.
        """

        result = self._bundle.initialize()
        statuses = dict(result.get("statuses", {}))
        diagnostics_raw = result.get("diagnostics", {})
        diagnostics: Dict[str, Any] = {}
        optional_fallbacks: list[tuple[str, Dict[str, Any]]] = []
        for layer, info in diagnostics_raw.items():
            entry = dict(info)
            attempts = [dict(attempt) for attempt in entry.get("attempts", [])]
            entry["attempts"] = attempts
            diagnostics[layer] = entry
            loaded_module = entry.get("loaded_module")
            if isinstance(loaded_module, str) and loaded_module.startswith(
                "memory.optional."
            ):
                optional_fallbacks.append((layer, entry))
        self.statuses = statuses
        self.diagnostics = diagnostics
        self.stubbed = bool(result.get("stubbed", self.stubbed))
        self.implementation = result.get("implementation", self.implementation)
        if self.stubbed:
            for layer in statuses:
                statuses[layer] = "skipped"
        self.fallback_reason = result.get("fallback_reason", self.fallback_reason)
        bundle_diag = {
            "implementation": self.implementation,
            "stubbed": self.stubbed,
            "source_module": _BUNDLE_SOURCE,
        }
        existing_bundle_diag = diagnostics_raw.get("__bundle__")
        if isinstance(existing_bundle_diag, dict):
            for key, value in existing_bundle_diag.items():
                bundle_diag.setdefault(key, value)
        if self.fallback_reason:
            bundle_diag["fallback_reason"] = self.fallback_reason
        if _IMPORT_ERROR is not None:
            bundle_diag["import_error"] = repr(_IMPORT_ERROR)
        diagnostics["__bundle__"] = bundle_diag
        if optional_fallbacks:
            summary_pairs = []
            for layer, entry in optional_fallbacks:
                module = entry.get("loaded_module")
                summary_pairs.append(f"{layer}:{module}")
                logger.warning(
                    "Optional memory stub activated",
                    extra={
                        "memory_layer": layer,
                        "fallback_module": module,
                        "fallback_reason": entry.get("fallback_reason"),
                        "layer_status": entry.get("status"),
                    },
                )
            logger.warning(
                "Optional memory modules loaded during initialization",
                extra={
                    "optional_layers": [layer for layer, _ in optional_fallbacks],
                    "optional_modules": [
                        entry.get("loaded_module") for _, entry in optional_fallbacks
                    ],
                    "optional_summary": ", ".join(summary_pairs),
                },
            )
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Aggregate memory queries via the Rust bundle."""
        return self._bundle.query(text)


__all__ = ["MemoryBundle"]
