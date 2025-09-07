from __future__ import annotations

import json
import time
from pathlib import Path

from distributed_memory import CycleCounterStore
from agents.event_bus import subscribe
from citadel.event_producer import Event

__all__ = ["HeartbeatLogger"]


class HeartbeatLogger:
    """Append chakra heartbeat cycles to a persistent log.

    Each received ``heartbeat`` event increments a per-chakra cycle counter
    stored via :class:`CycleCounterStore`. The updated cycle identifier and
    timestamp are written to ``logs/heartbeat.log`` in JSON lines format.
    """

    def __init__(
        self,
        store: CycleCounterStore | None = None,
        *,
        log_path: str | Path = "logs/heartbeat.log",
    ) -> None:
        self.store = store or CycleCounterStore(path="chakra_cycles.json")
        self.log_path = Path(log_path)

    async def listen(self) -> None:
        """Subscribe to global heartbeat events and record them."""

        async def handler(event: Event) -> None:
            if event.event_type != "heartbeat":
                return
            chakra = event.payload.get("chakra")
            if chakra:
                self.log(str(chakra))

        await subscribe(handler)

    def log(self, chakra: str, *, timestamp: float | None = None) -> int:
        """Record a cycle for ``chakra`` and return its identifier."""

        cycle_id = self.store.increment(chakra)
        entry = {
            "chakra": chakra,
            "cycle_id": cycle_id,
            "timestamp": timestamp or time.time(),
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry))
            fh.write("\n")
        return cycle_id
