# Patent pending – see PATENTS.md
"""Route questions to archetype-specific vector stores.

The module maps archetype labels to collection names and delegates
retrieval to :mod:`rag.retriever`. Calling :func:`route_query` triggers
lookup requests against the configured vector database.
"""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Dict, List

from rag import retriever as rag_retriever

_STORE_MAP = {
    "sage": "tech",
    "hero": "tech",
    "warrior": "ritual",
    "orphan": "ritual",
    "caregiver": "ritual",
    "citrinitas": "ritual",
    "jester": "music",
    "everyman": "music",
}


def _select_store(archetype: str) -> str:
    return _STORE_MAP.get(archetype.lower(), "tech")


def route_query(question: str, archetype: str) -> List[Dict]:
    """Return results for ``question`` using the store chosen by ``archetype``."""
    store = _select_store(archetype)
    return rag_retriever.retrieve_top(question, collection=store)


__all__ = ["route_query"]
