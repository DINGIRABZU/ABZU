"""Fallback cortex layer returning empty results."""

from __future__ import annotations

__version__ = "0.2.0"

from pathlib import Path
from typing import Any, Dict, List, Sequence

import hashlib

CORTEX_MEMORY_FILE = Path("data/cortex_memory_spiral.jsonl")
CORTEX_INDEX_FILE = Path("data/cortex_memory_index.json")
PATCH_LINKS_FILE = Path("data/patch_links.jsonl")


def record_spiral(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Discard spiral records."""


def search_index(*args: Any, **kwargs: Any) -> List[int]:
    """Return no matches."""
    return []


def link_patch_metadata(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Discard patch metadata."""


def hash_tag(tag: str) -> str:
    """Return a stable hash for ``tag``."""
    return hashlib.sha256(tag.encode("utf-8")).hexdigest()


def query_spirals(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty list as no cortex records are stored."""
    return []


def query_spirals_concurrent(
    requests: Sequence[Dict[str, Any]]
) -> List[List[Dict[str, Any]]]:
    """Return an empty result list for each request."""
    return [[] for _ in requests]


def prune_spirals(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """No stored spirals to prune."""


def export_spirals(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
    """Nothing to export."""


__all__ = [
    "record_spiral",
    "search_index",
    "link_patch_metadata",
    "hash_tag",
    "query_spirals",
    "query_spirals_concurrent",
    "prune_spirals",
    "export_spirals",
    "CORTEX_MEMORY_FILE",
    "CORTEX_INDEX_FILE",
    "PATCH_LINKS_FILE",
]
