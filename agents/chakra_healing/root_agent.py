"""Monitor root chakra metrics and trigger network restoration."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path

from agents.utils.story_adapter import get_recent_stories
from .base import heal, listen_for_heartbeat

CHAKRA = "root"
THRESHOLD = 0.8
SCRIPT_PATH = Path("scripts/chakra_healing/root_restore_network.sh")
AGENT_ID = "root_agent"
SUBCOMPONENTS: list[str] = []


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


def recent_stories(limit: int = 50) -> list[str]:
    """Return recent narrative stories for this agent."""
    return get_recent_stories(AGENT_ID, limit)


async def start_heartbeat_listener() -> None:
    """Listen for heartbeat events and emit confirmations."""
    await listen_for_heartbeat(CHAKRA, AGENT_ID, SUBCOMPONENTS)


__all__ = [
    "heal_if_needed",
    "recent_stories",
    "CHAKRA",
    "THRESHOLD",
    "SCRIPT_PATH",
    "AGENT_ID",
    "SUBCOMPONENTS",
    "start_heartbeat_listener",
]
