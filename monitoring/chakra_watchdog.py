"""Chakra heartbeat watchdog emitting events when chakras fall silent."""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, Mapping

from agents.event_bus import emit_event

LOGGER = logging.getLogger(__name__)


class ChakraWatchdog:
    """Poll chakra heartbeat metrics and emit ``chakra_down`` events."""

    def __init__(
        self,
        heartbeat_fn: Callable[[], Mapping[str, float]],
        threshold: float,
        poll_interval: float = 1.0,
        emitter: Callable[[str, str, Dict[str, float | str]], None] = emit_event,
    ) -> None:
        self.heartbeat_fn = heartbeat_fn
        self.threshold = threshold
        self.poll_interval = poll_interval
        self.emit = emitter

    def poll_once(self, *, now: float | None = None) -> None:
        """Check heartbeats and emit events for delayed chakras."""

        current = now or time.time()
        heartbeats = self.heartbeat_fn()
        for name, hb in heartbeats.items():
            delay = current - hb
            if delay > self.threshold:
                LOGGER.warning("Chakra %s missed heartbeat by %.2fs", name, delay)
                self.emit(
                    "chakra_watchdog",
                    "chakra_down",
                    {"chakra": name, "delay": delay},
                )

    def run(self) -> None:
        """Continuously poll for heartbeat delays."""

        while True:
            self.poll_once()
            time.sleep(self.poll_interval)


__all__ = ["ChakraWatchdog"]
