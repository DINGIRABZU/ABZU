"""Dispatch tasks to agents based on capabilities and triggers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

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


# ------------------------------------------------------------------
def run_mission(events: Iterable[Dict[str, Any]]) -> None:
    """Emit each mission event via the event bus.

    ``events`` is an iterable of dictionaries with ``event_type`` and optional
    ``payload`` keys. Each entry is forwarded as an event from the
    ``mission_control`` actor.
    """

    for entry in events:
        emit_event(
            "mission_control",
            entry.get("event_type", ""),
            entry.get("payload", {}),
        )


def run_mission_file(path: str | Path) -> None:
    """Load mission definitions from ``path`` and dispatch them."""

    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):  # pragma: no cover - simple validation
        raise ValueError("Mission file must contain a list of events")
    run_mission(data)


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Dispatch mission events")
    parser.add_argument("mission", help="Path to mission JSON file")
    args = parser.parse_args()
    run_mission_file(args.mission)


__all__ = ["TaskOrchestrator", "run_mission", "run_mission_file"]
