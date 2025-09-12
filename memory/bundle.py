# Patent pending – see PATENTS.md
"""Thin wrapper around the Rust memory bundle."""

from __future__ import annotations

from typing import Any, Dict

from neoabzu_memory import MemoryBundle as _RustBundle

__version__ = "0.2.0"


class MemoryBundle:
    """Proxy class delegating to the Rust implementation."""

    def __init__(self) -> None:
        self._bundle = _RustBundle()
        self.statuses: Dict[str, str] = {}

    def initialize(self) -> Dict[str, str]:
        """Initialize memory layers through the Rust bundle."""
        statuses = self._bundle.initialize()
        self.statuses = dict(statuses)
        return statuses

    def query(self, text: str) -> Dict[str, Any]:
        """Aggregate memory queries via the Rust bundle."""
        return self._bundle.query(text)


__all__ = ["MemoryBundle"]
