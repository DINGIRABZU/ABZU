# Patent pending – see PATENTS.md
"""Thin wrapper around the Rust memory bundle."""

from __future__ import annotations

import logging
from typing import Any, Dict

from neoabzu_memory import MemoryBundle as _RustBundle

__version__ = "0.2.0"


logger = logging.getLogger("memory.bundle")


class MemoryBundle:
    """Proxy class delegating to the Rust implementation."""

    def __init__(self) -> None:
        self._bundle = _RustBundle()
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
