"""Cocytus prompt arbitration utilities.

Responsibilities:
- logical sanitization
- legal parsing
- audit model bias
"""

from __future__ import annotations

from typing import Any, Dict

from ..event_bus import emit_event


def arbitrate(actor: str, action: str, entity_eval: Dict[str, Any]) -> None:
    """Escalate a non-compliant action for Cocytus arbitration."""

    emit_event(
        "cocytus",
        "arbitration",
        {"actor": actor, "action": action, "entity": entity_eval},
    )


__all__ = ["arbitrate"]
