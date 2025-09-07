from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Mapping

from citadel.event_producer import Event

from agents.nazarick.avatar_resuscitator import AvatarResuscitator
from monitoring.avatar_watchdog import AvatarWatchdog


def test_normal_operation() -> None:
    now = time.time()
    frames = {"sess": now}
    heartbeats = {"sess": now}

    def get_frames() -> Mapping[str, float]:
        return frames

    def get_heartbeats() -> Mapping[str, float]:
        return heartbeats

    events: List[Event] = []

    def capture(actor: str, action: str, payload: Dict[str, float | str]) -> None:
        events.append(Event(agent_id=actor, event_type=action, payload=payload))

    wd = AvatarWatchdog(get_frames, get_heartbeats, threshold=5, emitter=capture)
    wd.poll_once(now=now + 1)
    assert events == []


def test_stalled_session_triggers_resuscitator() -> None:
    now = time.time()
    frames = {"sess": now - 10}
    heartbeats = {"sess": now - 10}

    def get_frames() -> Mapping[str, float]:
        return frames

    def get_heartbeats() -> Mapping[str, float]:
        return heartbeats

    events: List[Event] = []

    def capture(actor: str, action: str, payload: Dict[str, float | str]) -> None:
        events.append(Event(agent_id=actor, event_type=action, payload=payload))

    wd = AvatarWatchdog(get_frames, get_heartbeats, threshold=5, emitter=capture)
    wd.poll_once(now=now)

    assert events and events[0].event_type == "avatar_down"

    called: Dict[str, bool] = {}

    def restart() -> bool:
        called["sess"] = True
        return True

    resuscitator = AvatarResuscitator({"sess": restart}, emitter=lambda *_: None)
    asyncio.run(resuscitator.handle_event(events[0]))

    assert called.get("sess") is True
