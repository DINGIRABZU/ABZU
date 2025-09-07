"""Record chakra heartbeat timestamps and report synchronization status."""

from __future__ import annotations

import time
from typing import Dict, Iterable, List

from distributed_memory import DistributedMemory


class ChakraHeartbeat:
    """Track last heartbeat per chakra with optional Redis persistence."""

    def __init__(
        self,
        chakras: Iterable[str] | None = None,
        *,
        window: float = 5.0,
        memory: DistributedMemory | None = None,
    ) -> None:
        try:
            self._memory = memory or DistributedMemory(key="chakra_heartbeat")
        except Exception:  # pragma: no cover - redis optional
            self._memory = None
        self.window = window
        self._cache: Dict[str, float] = {}
        self._confirm: Dict[str, float] = {}
        self._chakras = set(chakras or [])

    def beat(self, chakra: str, timestamp: float | None = None) -> None:
        """Record a heartbeat for ``chakra`` at ``timestamp``."""

        ts = timestamp or time.time()
        self._chakras.add(chakra)
        self._cache[chakra] = ts
        if self._memory is not None:
            self._memory.client.hset(self._memory.key, chakra, ts)

    def heartbeats(self) -> Dict[str, float]:
        """Return mapping of chakras to their last seen heartbeat."""

        beats = dict(self._cache)
        if self._memory is not None:
            data = self._memory.client.hgetall(self._memory.key)
            for key, val in data.items():
                name = key.decode() if hasattr(key, "decode") else key
                beats[name] = float(val)
        return beats

    def confirm(self, chakra: str, timestamp: float | None = None) -> None:
        """Record a pulse confirmation for ``chakra``."""

        ts = timestamp or time.time()
        self._chakras.add(chakra)
        self._confirm[chakra] = ts

    def pending(self, *, now: float | None = None) -> List[str]:
        """Return chakras missing confirmation beyond the window."""

        current = now or time.time()
        missing: List[str] = []
        for chakra in self._chakras:
            beat_ts = self._cache.get(chakra)
            confirm_ts = self._confirm.get(chakra, 0.0)
            if beat_ts and confirm_ts < beat_ts and current - beat_ts > self.window:
                missing.append(chakra)
        return missing

    def check_alerts(self, *, now: float | None = None) -> None:
        """Raise an alert if any chakra has not confirmed its pulse."""

        missing = self.pending(now=now)
        if missing:
            raise RuntimeError(f"Missing pulse confirmations: {', '.join(missing)}")

    def sync_status(self, *, now: float | None = None) -> str:
        """Return ``aligned`` when all chakras reported recently."""

        if not self._chakras:
            return "aligned"
        current = now or time.time()
        beats = self.heartbeats()
        for chakra in self._chakras:
            ts = beats.get(chakra)
            if ts is None or current - ts > self.window:
                return "out_of_sync"
        return "aligned"


__all__ = ["ChakraHeartbeat"]
