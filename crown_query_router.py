from __future__ import annotations

"""Route questions to the appropriate vector collection."""

from typing import List, Dict

import rag_retriever

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
