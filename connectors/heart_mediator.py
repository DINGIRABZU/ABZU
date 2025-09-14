"""Heart mediator routing Head↔Base communications."""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Dict

from .signal_bus import publish


def mediate_head_base(head_msg: str, base_msg: str) -> Dict[str, str]:
    """Relay messages between Head and Base via the Heart channel."""
    payload = {"head": head_msg, "base": base_msg}
    publish("heart:coordination", payload, 0)
    return payload


__all__ = ["mediate_head_base"]
