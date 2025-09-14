"""Emit structured Bana narrative events.

Helpers here validate interaction data, persist it via the narrative engine,
and broadcast it on the shared agent event bus so downstream consumers like
``nazarick.narrative_scribe`` can compose prose.
"""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict, Optional

from .event_structurizer import from_interaction
from agents.event_bus import emit_event as bus_emit
from memory import narrative_engine


def emit(
    agent_id: str,
    event_type: str,
    payload: Dict[str, Any],
    *,
    timestamp: Optional[str] = None,
    target_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and dispatch a narrative ``event``.

    The structured event is stored through :mod:`memory.narrative_engine` and
    also emitted on the global event bus for other agents.
    """

    event = from_interaction(agent_id, event_type, payload, timestamp=timestamp)
    narrative_engine.log_event(event)
    metadata = dict(payload)
    if target_agent:
        metadata["target_agent"] = target_agent
    bus_emit(agent_id, event_type, metadata)
    return event


__all__ = ["emit"]
