"""Emit periodic heartbeat events for all chakras."""

from __future__ import annotations

import asyncio
from typing import Iterable, Sequence

from agents.event_bus import emit_event

__version__ = "0.1.0"

CHAKRAS: Sequence[str] = (
    "root",
    "sacral",
    "solar",
    "heart",
    "throat",
    "third_eye",
    "crown",
)
DEFAULT_INTERVAL = 5.0


async def emit_pulse(
    interval: float = DEFAULT_INTERVAL, chakras: Iterable[str] = CHAKRAS
) -> None:
    """Continuously broadcast heartbeat events for ``chakras``."""
    names = tuple(chakras)
    while True:
        for chakra in names:
            emit_event("pulse_emitter", "heartbeat", {"chakra": chakra})
        await asyncio.sleep(interval)


def run(interval: float = DEFAULT_INTERVAL, chakras: Iterable[str] = CHAKRAS) -> None:
    """Run :func:`emit_pulse` in an ``asyncio`` event loop."""
    asyncio.run(emit_pulse(interval=interval, chakras=chakras))


__all__ = ["emit_pulse", "run", "CHAKRAS", "DEFAULT_INTERVAL"]
