"""Avatar session watchdog emitting events when streams stall."""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, Mapping

from agents.event_bus import emit_event

LOGGER = logging.getLogger(__name__)
__version__ = "0.1.0"


class AvatarWatchdog:
    """Poll avatar frame and heartbeat timestamps and emit ``avatar_down`` events."""

    def __init__(
        self,
        frame_fn: Callable[[], Mapping[str, float]],
        heartbeat_fn: Callable[[], Mapping[str, float]],
        threshold: float,
        poll_interval: float = 1.0,
        emitter: Callable[[str, str, Dict[str, float | str]], None] = emit_event,
    ) -> None:
        self.frame_fn = frame_fn
        self.heartbeat_fn = heartbeat_fn
        self.threshold = threshold
        self.poll_interval = poll_interval
        self.emit = emitter

    def poll_once(self, *, now: float | None = None) -> None:
        """Check sessions and emit events for stalled avatars."""

        current = now or time.time()
        frames = self.frame_fn()
        heartbeats = self.heartbeat_fn()
        sessions = set(frames) | set(heartbeats)
        for session in sessions:
            frame_ts = frames.get(session)
            hb_ts = heartbeats.get(session)
            frame_delay = current - frame_ts if frame_ts is not None else float("inf")
            hb_delay = current - hb_ts if hb_ts is not None else float("inf")
            delay = max(frame_delay, hb_delay)
            if delay > self.threshold:
                LOGGER.warning(
                    "Session %s stalled: frame %.2fs heartbeat %.2fs",
                    session,
                    frame_delay,
                    hb_delay,
                )
                payload: Dict[str, float | str] = {
                    "session": session,
                    "frame_delay": frame_delay,
                    "heartbeat_delay": hb_delay,
                }
                self.emit("avatar_watchdog", "avatar_down", payload)

    def run(self) -> None:
        """Continuously poll for stalled sessions."""

        while True:
            self.poll_once()
            time.sleep(self.poll_interval)


__all__ = ["AvatarWatchdog"]
