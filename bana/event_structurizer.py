"""Translate Bana interactions into schema-validated events."""

from __future__ import annotations

__version__ = "0.1.0"

from datetime import datetime
from typing import Any, Dict
import jsonschema

# Public JSON schema for narrative events
EVENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "time": {"type": "string", "format": "date-time"},
        "agent_id": {"type": "string"},
        "event_type": {"type": "string"},
        "payload": {"type": "object"},
    },
    "required": ["time", "agent_id", "event_type", "payload"],
    "additionalProperties": False,
}


def _validate(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ``event`` against :data:`EVENT_SCHEMA`."""
    jsonschema.validate(event, EVENT_SCHEMA)
    return event


def from_interaction(
    agent_id: str,
    event_type: str,
    payload: Dict[str, Any],
    *,
    timestamp: str | None = None,
) -> Dict[str, Any]:
    """Create an event from an interaction payload."""
    event = {
        "time": timestamp or datetime.utcnow().isoformat() + "Z",
        "agent_id": agent_id,
        "event_type": event_type,
        "payload": payload,
    }
    return _validate(event)


def from_biosignal_row(
    row: Dict[str, Any], agent_id: str, event_type: str
) -> Dict[str, Any]:
    """Translate a biosignal ``row`` into an event."""
    timestamp = row.get("timestamp") or datetime.utcnow().isoformat() + "Z"
    payload = {k: v for k, v in row.items() if k != "timestamp"}
    event = {
        "time": timestamp,
        "agent_id": agent_id,
        "event_type": event_type,
        "payload": payload,
    }
    return _validate(event)


__all__ = ["EVENT_SCHEMA", "from_interaction", "from_biosignal_row"]
