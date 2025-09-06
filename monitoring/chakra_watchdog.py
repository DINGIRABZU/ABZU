"""Chakra heartbeat watchdog emitting events when chakras fall silent."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable, Dict, Mapping

from agents.event_bus import emit_event

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram
    from agents.razar.health_checks import init_metrics as _init_metrics

    _init_metrics()
except Exception:  # pragma: no cover - metrics are optional
    Counter = Histogram = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)

_registry_path = (
    Path(__file__).resolve().parents[1] / "agents" / "nazarick" / "agent_registry.json"
)

POLL_COUNTER = (
    Counter("chakra_watchdog_polls_total", "Total watchdog poll cycles")
    if Counter
    else None
)
POLL_DURATION = (
    Histogram(
        "chakra_watchdog_poll_seconds", "Duration of watchdog poll cycles in seconds"
    )
    if Histogram
    else None
)
CHAKRA_DOWN_COUNTER = (
    Counter(
        "chakra_watchdog_chakra_down_total",
        "Number of chakra_down events emitted",
        ["chakra"],
    )
    if Counter
    else None
)


def _load_chakra_mapping() -> Dict[str, str]:
    """Load the chakra→agent mapping from the registry file."""

    try:
        data = json.loads(_registry_path.read_text())
    except FileNotFoundError:
        LOGGER.warning("Agent registry not found at %s", _registry_path)
        return {}
    except Exception as exc:  # pragma: no cover - unexpected errors
        LOGGER.warning("Failed to load agent registry from %s: %s", _registry_path, exc)
        return {}
    return {entry["chakra"]: entry["id"] for entry in data.get("agents", [])}


CHAKRA_TO_AGENT = _load_chakra_mapping()


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

        start = time.time()
        current = now or start
        heartbeats = self.heartbeat_fn()
        if POLL_COUNTER is not None:
            POLL_COUNTER.inc()
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
                if CHAKRA_DOWN_COUNTER is not None:
                    CHAKRA_DOWN_COUNTER.labels(name).inc()
                self.emit("chakra_watchdog", "chakra_down", payload)
        if POLL_DURATION is not None:
            POLL_DURATION.observe(time.time() - start)

    def run(self) -> None:
        """Continuously poll for heartbeat delays."""

        while True:
            self.poll_once()
            time.sleep(self.poll_interval)


__all__ = ["ChakraWatchdog"]
