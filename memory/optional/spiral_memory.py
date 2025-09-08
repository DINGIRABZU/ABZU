"""No-op spiral memory used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path
from typing import Iterable, Mapping, Sequence

REGISTRY_DB = Path("data/spiral_registry.db")


class SpiralMemory:
    """Stubbed spiral memory that discards all inputs."""

    def __init__(self, db_path: Path = REGISTRY_DB, width: int = 16) -> None:
        self.db_path = db_path
        self.width = width

    def add_layer(self, data: Sequence[float]) -> None:  # pragma: no cover - stub
        """Ignore added memory ``data``."""

    def aggregate(self) -> list[float]:  # pragma: no cover - stub
        """Return an empty aggregate."""
        return []

    def register_event(
        self, event: str, layers: Mapping[str, Iterable[float]] | None = None
    ) -> None:  # pragma: no cover - stub
        """Ignore spiral events."""

    def recall(self, query: str) -> str:
        """Return an empty insight for ``query``."""
        return ""


DEFAULT_MEMORY = SpiralMemory()


def spiral_recall(query: str) -> str:
    """Expose :class:`SpiralMemory` recall via module-level function."""
    return DEFAULT_MEMORY.recall(query)


__all__ = ["SpiralMemory", "spiral_recall", "REGISTRY_DB"]
