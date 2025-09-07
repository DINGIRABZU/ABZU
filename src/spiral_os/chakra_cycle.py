"""Chakra gear ratios with persistent heartbeat scheduler."""

from __future__ import annotations

__version__ = "0.1.2"

import asyncio
import time
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List

from distributed_memory import CycleCounterStore

# Nominal gear ratios for each chakra in the cycle
GEAR_RATIOS: Dict[str, float] = {
    "root": 1.0,
    "sacral": 1.2,
    "solar": 1.5,
    "heart": 1.0,
    "throat": 0.8,
    "third_eye": 1.3,
    "crown": 1.0,
}


@dataclass
class Heartbeat:
    """Heartbeat event emitted by the scheduler."""

    chakra: str
    cycle_count: int
    timestamp: float


class ChakraCycle:
    """Maintain chakra cycle counts and emit heartbeat events."""

    def __init__(
        self,
        store: CycleCounterStore | None = None,
        interval: float = 5.0,
    ) -> None:
        self.store = store or CycleCounterStore()
        self.interval = interval
        # Load persisted cycle counts and ensure all chakras are present
        self.cycle_counts: Dict[str, int] = self.store.load()
        for chakra in GEAR_RATIOS:
            self.cycle_counts.setdefault(chakra, 0)

    # ------------------------------------------------------------------
    def get_cycle(self, chakra: str) -> int:
        """Return the current cycle count for ``chakra``."""

        return self.cycle_counts.get(chakra, 0)

    # ------------------------------------------------------------------
    def emit_heartbeat(self) -> List[Heartbeat]:
        """Increment cycle counts and return heartbeat events."""

        ts = time.time()
        events: List[Heartbeat] = []
        for chakra in GEAR_RATIOS:
            count = self.store.increment(chakra)
            self.cycle_counts[chakra] = count
            events.append(Heartbeat(chakra, count, ts))
        return events

    # ------------------------------------------------------------------
    async def scheduler(self) -> AsyncIterator[Heartbeat]:
        """Asynchronously emit heartbeat events at ``interval`` seconds."""

        while True:
            for event in self.emit_heartbeat():
                yield event
            await asyncio.sleep(self.interval)


_default_cycle = ChakraCycle()


def get_cycle(chakra: str) -> int:
    """Convenience wrapper for the default :class:`ChakraCycle`."""

    return _default_cycle.get_cycle(chakra)


def emit_heartbeat() -> List[Heartbeat]:
    """Emit a heartbeat using the default :class:`ChakraCycle`."""

    return _default_cycle.emit_heartbeat()


__all__ = [
    "GEAR_RATIOS",
    "Heartbeat",
    "ChakraCycle",
    "get_cycle",
    "emit_heartbeat",
]
