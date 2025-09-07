"""Expose agent heartbeat summaries."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter

from .agent_heartbeat import AgentHeartbeat

router = APIRouter()

# Shared heartbeat tracker
heartbeat = AgentHeartbeat()

# Placeholder mappings for last actions and chakra alignment
_last_actions: Dict[str, str] = {}
_chakras: Dict[str, str] = {}


def _collect(now: float | None = None) -> Dict[str, Any]:
    """Collect heartbeat timestamps and status information."""

    current = now or time.time()
    beats = heartbeat.heartbeats()
    agents: Dict[str, Dict[str, float | str]] = {}
    for name, ts in beats.items():
        agents[name] = {
            "last_beat": ts,
            "last_action": _last_actions.get(name, "unknown"),
            "chakra": _chakras.get(name, "unknown"),
        }
    return {"agents": agents, "timestamp": current}


@router.get("/agents/status")
def agent_status() -> Dict[str, Any]:
    """Return current agent heartbeat information as JSON."""

    return _collect()


__all__ = ["router", "heartbeat"]
