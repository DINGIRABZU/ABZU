"""Stub interfaces for DATPars parsers."""

from __future__ import annotations

from typing import Any, Protocol


class DataParser(Protocol):
    """Parse raw sources into structured records."""

    def parse(self, source: str) -> dict[str, Any]:
        """Parse ``source`` and return a structured representation."""


class ParserFactory(Protocol):
    """Create parser instances for specific formats."""

    def create(self, name: str) -> DataParser:
        """Return a parser for the given format ``name``."""
