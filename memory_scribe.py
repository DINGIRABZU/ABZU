"""Interface for recording embeddings in vector memory.

The Memory Scribe manages vector memory interactions within the Heart layer.
"""

from __future__ import annotations

import logging

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except Exception:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]

vector_memory = _vector_memory
logger = logging.getLogger(__name__)


def store_embedding(text: str) -> None:
    """Embed ``text`` and persist it to the vector memory backend.

    Uses :func:`vector_memory.add` when available and falls back to
    :func:`vector_memory.add_vector` for older backends.
    """
    if vector_memory is None:
        logger.warning("vector memory backend unavailable")
        return
    try:
        if hasattr(vector_memory, "add"):
            vector_memory.add(text)
        else:
            vector_memory.add_vector(text, {})
    except Exception:  # pragma: no cover - best effort logging
        logger.warning("vector memory add failed", exc_info=True)


__all__ = ["store_embedding"]
if vector_memory is not None:
    __all__.append("vector_memory")
