"""Chakra heartbeat watchdog emitting events when chakras fall silent."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable, Dict, Mapping

from agents.event_bus import emit_event

LOGGER = logging.getLogger(__name__)

_registry_path = (
    Path(__file__).resolve().parents[1] / "agents" / "nazarick" / "agent_registry.json"
)

try:
    _registry_data = json.loads(_registry_path.read_text())
    CHAKRA_TO_AGENT = {
        entry["chakra"]: entry["id"] for entry in _registry_data.get("agents", [])
    }
except FileNotFoundError:
    LOGGER.warning("Agent registry not found at %s", _registry_path)
    CHAKRA_TO_AGENT = {}
except Exception as exc:  # pragma: no cover - unexpected errors
    LOGGER.warning("Failed to load agent registry from %s: %s", _registry_path, exc)
    CHAKRA_TO_AGENT = {}


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
                payload: Dict[str, float | str] = {"chakra": name, "delay": delay}
                agent_id = CHAKRA_TO_AGENT.get(name)
                if agent_id:
                    payload["target_agent"] = agent_id
                else:
                    LOGGER.warning("No agent mapping found for chakra %s", name)
                self.emit("chakra_watchdog", "chakra_down", payload)

    def run(self) -> None:
        """Continuously poll for heartbeat delays."""

        while True:
            self.poll_once()
            time.sleep(self.poll_interval)


__all__ = ["ChakraWatchdog"]
