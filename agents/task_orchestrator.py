"""Dispatch tasks to agents based on capabilities and triggers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from citadel.event_producer import Event

from .event_bus import emit_event, subscribe


REGISTRY_FILE = Path(__file__).parent / "nazarick" / "agent_registry.json"


class TaskOrchestrator:
    """Route events to agents advertising matching capabilities and triggers."""

    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or REGISTRY_FILE
        self.capability_map: Dict[str, List[str]] = {}
        self.trigger_map: Dict[str, List[str]] = {}
        self._load_registry()

    # ------------------------------------------------------------------
    # Registry handling
    def _load_registry(self) -> None:
        data = json.loads(Path(self.registry_path).read_text())
        for entry in data.get("agents", []):
            agent_id = entry.get("id")
            for capability in entry.get("capabilities", []):
                self.capability_map.setdefault(capability, []).append(agent_id)
            for trigger in entry.get("triggers", []):
                self.trigger_map.setdefault(trigger, []).append(agent_id)

    # ------------------------------------------------------------------
    async def handle_event(self, event: Event) -> None:
        """Forward ``event`` to matching agents via the event bus."""

        capability = event.payload.get("capability")
        if capability is None:
            return

        candidates = self.capability_map.get(capability, [])
        triggered = self.trigger_map.get(event.event_type, [])
        for agent_id in [a for a in candidates if a in triggered]:
            emit_event(
                "task_orchestrator",
                "dispatch",
                {
                    "target_agent": agent_id,
                    "capability": capability,
                    "payload": event.payload,
                },
            )

    # ------------------------------------------------------------------
    async def run(self) -> None:
        """Continuously consume events from the bus."""

        await subscribe(self.handle_event)


__all__ = ["TaskOrchestrator"]
