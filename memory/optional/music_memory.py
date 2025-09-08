"""No-op music memory layer used when the real implementation is unavailable."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict, List, Sequence

Vector = Sequence[float]


def add_track(
    embedding: Vector,
    metadata: Dict[str, Any],
    emotion: str,
    *,
    track_id: str | None = None,
    db_path: Any | None = None,
) -> str:
    """Discard music tracks and return an empty identifier."""
    return track_id or ""


def query_tracks(
    embedding: Vector,
    *,
    k: int = 5,
    emotion: str | None = None,
    db_path: Any | None = None,
) -> List[Dict[str, Any]]:
    """Return an empty list as no tracks are stored."""
    return []


__all__ = ["add_track", "query_tracks", "Vector"]
