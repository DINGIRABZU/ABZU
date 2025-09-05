"""Core agent packages for ABZU."""

from __future__ import annotations

import pkgutil
from pathlib import Path

from worlds.config_registry import register_agent
from .event_bus import emit_event, set_event_producer


def _discover_agents() -> tuple[str, ...]:
    base = Path(__file__).resolve().parent
    agents = []
    for module in pkgutil.iter_modules([str(base)]):
        if module.ispkg and not module.name.startswith("_"):
            agents.append(module.name)
    return tuple(sorted(agents))


AGENTS = _discover_agents()
for _agent in AGENTS:
    register_agent(_agent)


__all__ = ["emit_event", "set_event_producer", "AGENTS"]
