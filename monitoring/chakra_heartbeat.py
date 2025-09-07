"""Record chakra heartbeat timestamps and report synchronization status."""

from __future__ import annotations

import time
from typing import Dict, Iterable, List

from distributed_memory import DistributedMemory

from agents.event_bus import emit_event, subscribe
from citadel.event_producer import Event

__version__ = "0.3.0"

try:  # pragma: no cover - metrics optional
    from prometheus_client import Counter, Gauge
except Exception:  # pragma: no cover - metrics optional
    Counter = Gauge = None  # type: ignore[assignment]


BEAT_COUNTER = (
    Counter("chakra_heartbeats_total", "Total heartbeat events", ["chakra"])
    if Counter
    else None
)
LAST_BEAT_GAUGE = (
    Gauge("chakra_last_heartbeat_timestamp", "Timestamp of last heartbeat", ["chakra"])
    if Gauge
    else None
)
CONFIRM_COUNTER = (
    Counter(
        "chakra_pulse_confirmations_total",
        "Total pulse confirmations",
        ["chakra"],
    )
    if Counter
    else None
)
LAST_CONFIRM_GAUGE = (
    Gauge(
        "chakra_last_confirmation_timestamp",
        "Timestamp of last pulse confirmation",
        ["chakra"],
    )
    if Gauge
    else None
)


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
        self._aligned = False

    async def listen(self) -> None:
        """Subscribe to global heartbeat events and update timestamps.

        The call blocks while the underlying :func:`subscribe` yields events and
        should typically be executed in a background task. It may be cancelled
        by the caller to stop monitoring.
        """

        async def handler(event: Event) -> None:
            if event.event_type != "heartbeat":
                return
            chakra = event.payload.get("chakra")
            if chakra:
                ts = float(event.payload.get("timestamp", time.time()))
                self.beat(str(chakra), ts)

        await subscribe(handler)

    def beat(self, chakra: str, timestamp: float | None = None) -> None:
        """Record a heartbeat for ``chakra`` at ``timestamp``."""

        ts = timestamp or time.time()
        self._chakras.add(chakra)
        self._cache[chakra] = ts
        if self._memory is not None:
            self._memory.client.hset(self._memory.key, chakra, ts)
        if BEAT_COUNTER is not None:
            BEAT_COUNTER.labels(chakra).inc()
        if LAST_BEAT_GAUGE is not None:
            LAST_BEAT_GAUGE.labels(chakra).set(ts)

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
        if CONFIRM_COUNTER is not None:
            CONFIRM_COUNTER.labels(chakra).inc()
        if LAST_CONFIRM_GAUGE is not None:
            LAST_CONFIRM_GAUGE.labels(chakra).set(ts)

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
        """Emit ``chakra_down`` events for missing confirmations."""

        missing = self.pending(now=now)
        for chakra in missing:
            emit_event("chakra_heartbeat", "chakra_down", {"chakra": chakra})
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
                self._aligned = False
                return "out_of_sync"
        if not self._aligned:
            self._aligned = True
            emit_event("chakra_heartbeat", "great_spiral", {"timestamp": current})
        return "aligned"


__all__ = ["ChakraHeartbeat"]
