"""Monitor sacral chakra metrics and reset GPU tasks."""

from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path

from agents.utils.story_adapter import get_recent_stories
from .base import heal, listen_for_heartbeat

CHAKRA = "sacral"
THRESHOLD = 0.85
SCRIPT_PATH = Path("scripts/chakra_healing/sacral_gpu_recover.py")
AGENT_ID = "sacral_agent"


def heal_if_needed() -> bool:
    return heal(CHAKRA, THRESHOLD, SCRIPT_PATH)


def recent_stories(limit: int = 50) -> list[str]:
    """Return recent narrative stories for this agent."""
    return get_recent_stories(AGENT_ID, limit)


async def start_heartbeat_listener() -> None:
    """Listen for heartbeat events and emit confirmations."""
    await listen_for_heartbeat(CHAKRA, AGENT_ID)


__all__ = [
    "heal_if_needed",
    "recent_stories",
    "CHAKRA",
    "THRESHOLD",
    "SCRIPT_PATH",
    "AGENT_ID",
    "start_heartbeat_listener",
]
