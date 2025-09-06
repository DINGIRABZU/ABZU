from __future__ import annotations

"""Lightweight experience replay using :mod:`vector_memory`.

Agent interactions are logged via :mod:`agents.interaction_log` and, when
available, stored in the vector database for later retrieval. The
:func:`replay` function provides similarity search over an agent's past
interactions so callers can supply contextual lessons before responding.
"""

from typing import List

from .interaction_log import log_agent_interaction

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except Exception:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]

vector_memory = _vector_memory


def store_event(agent_id: str, text: str) -> None:
    """Record ``text`` for ``agent_id`` in logs and vector memory."""
    entry = {
        "agent_id": agent_id,
        "text": text,
        "function": "experience_replay.store_event",
    }
    log_agent_interaction(entry)
    if vector_memory is None:
        return
    try:  # pragma: no cover - best effort
        vector_memory.add_vector(text, {"agent_id": agent_id})
    except Exception:  # pragma: no cover - ignore storage failures
        pass


def replay(agent_id: str, query: str, *, k: int = 5) -> List[str]:
    """Return up to ``k`` past events for ``agent_id`` similar to ``query``."""
    if vector_memory is None:
        return []
    try:  # pragma: no cover - best effort
        hits = vector_memory.search(
            query, filter={"agent_id": agent_id}, k=k, scoring="similarity"
        )
    except Exception:  # pragma: no cover - ignore search failures
        return []
    return [hit.get("text", "") for hit in hits]


__all__ = ["store_event", "replay"]
