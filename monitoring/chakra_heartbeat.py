"""Monitor chakra heartbeat metrics and detect alignment.

This module polls heartbeat gauges emitted by :mod:`spiral_os.chakra_cycle`
 and records the last-seen timestamp for each chakra via
:class:`distributed_memory.DistributedMemory`.  When all chakras report
heartbeats within a configured threshold, a ``synchronized`` event is
broadcast.
"""

from __future__ import annotations

import asyncio
import time
from typing import Mapping, Any

from distributed_memory import DistributedMemory
from spiral_os.chakra_cycle import GEAR_RATIOS

try:  # pragma: no cover - optional dependency
    from operator_api import broadcast_event
except Exception:  # pragma: no cover - optional dependency

    async def broadcast_event(event: dict[str, object]) -> None:
        """Fallback no-op when operator_api is unavailable."""
        return None


__version__ = "0.1.0"


class ChakraHeartbeat:
    """Persist chakra heartbeats and report synchronization status."""

    _memory: Any | None = None
    _threshold: float = 0.5

    # ------------------------------------------------------------------
    @classmethod
    def configure(
        cls, *, memory: Any | None = None, threshold: float | None = None
    ) -> None:
        """Configure backing memory and alignment threshold."""
        if memory is not None:
            cls._memory = memory
        if threshold is not None:
            cls._threshold = threshold
        if cls._memory is None:
            try:
                cls._memory = DistributedMemory(key="chakra_heartbeat")
            except Exception:  # pragma: no cover - redis optional
                cls._memory = None

    # ------------------------------------------------------------------
    @classmethod
    def poll(
        cls, metrics: Mapping[str, float], *, timestamp: float | None = None
    ) -> None:
        """Persist ``metrics`` with ``timestamp`` for each chakra."""
        if cls._memory is None:
            cls.configure()
        if cls._memory is None:
            return
        ts = timestamp or time.time()
        for name in metrics:
            cls._memory.backup(name, [], {"timestamp": ts})

    # ------------------------------------------------------------------
    @classmethod
    def sync_status(cls) -> bool:
        """Return ``True`` if all chakras are aligned within the threshold."""
        if cls._memory is None:
            cls.configure()
        if cls._memory is None:
            return False
        data = cls._memory.restore()
        if len(data) < len(GEAR_RATIOS):
            return False
        times = [meta.get("timestamp", 0.0) for _, (_, meta) in data.items()]
        if not times:
            return False
        aligned = max(times) - min(times) <= cls._threshold
        if aligned:
            asyncio.run(broadcast_event({"event": "synchronized"}))
        return aligned


__all__ = ["ChakraHeartbeat"]
