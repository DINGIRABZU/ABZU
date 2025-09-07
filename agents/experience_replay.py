from __future__ import annotations

"""Lightweight experience replay using the chakra registry.

Agent interactions are logged via :mod:`agents.interaction_log` and, when
available, stored in the chakra-aware vector database for later retrieval. The
:func:`replay` function provides similarity search over an agent's past
interactions so callers can supply contextual lessons before responding. All
events are tagged with a ``chakra`` to allow energetic filtering.
"""

from typing import List

from .interaction_log import log_agent_interaction

try:  # pragma: no cover - optional dependency
    from memory.chakra_registry import ChakraRegistry
except Exception:  # pragma: no cover - optional dependency
    ChakraRegistry = None  # type: ignore[assignment]

chakra_registry = ChakraRegistry() if ChakraRegistry is not None else None


def store_event(agent_id: str, text: str, chakra: str = "root") -> None:
    """Record ``text`` for ``agent_id`` in logs and chakra registry."""
    entry = {
        "agent_id": agent_id,
        "text": text,
        "function": "experience_replay.store_event",
    }
    log_agent_interaction(entry)
    if chakra_registry is None:
        return
    try:  # pragma: no cover - best effort
        chakra_registry.record(chakra, text, agent_id, agent_id=agent_id)
    except Exception:  # pragma: no cover - ignore storage failures
        pass


def replay(agent_id: str, query: str, *, k: int = 5, chakra: str = "root") -> List[str]:
    """Return up to ``k`` past events for ``agent_id`` similar to ``query``."""
    if chakra_registry is None:
        return []
    try:  # pragma: no cover - best effort
        hits = chakra_registry.search(
            chakra, query, filter={"agent_id": agent_id}, k=k, scoring="similarity"
        )
    except Exception:  # pragma: no cover - ignore search failures
        return []
    return [hit.get("text", "") for hit in hits]


__all__ = ["store_event", "replay"]
