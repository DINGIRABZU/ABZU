from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Mapping

from citadel.event_producer import Event

from monitoring.chakra_watchdog import ChakraWatchdog
from agents.nazarick.chakra_resuscitator import ChakraResuscitator


def test_normal_operation() -> None:
    now = time.time()
    heartbeats = {"root": now, "crown": now}

    def get_heartbeats() -> Mapping[str, float]:
        return heartbeats

    events: List[Event] = []

    def capture(actor: str, action: str, payload: Dict[str, float | str]) -> None:
        events.append(Event(agent_id=actor, event_type=action, payload=payload))

    wd = ChakraWatchdog(get_heartbeats, threshold=5, emitter=capture)
    wd.poll_once(now=now + 1)
    assert events == []


def test_trigger_resuscitator(caplog) -> None:
    now = time.time()
    heartbeats = {"root": now - 10, "crown": now}

    def get_heartbeats() -> Mapping[str, float]:
        return heartbeats

    events: List[Event] = []

    def capture(actor: str, action: str, payload: Dict[str, float | str]) -> None:
        events.append(Event(agent_id=actor, event_type=action, payload=payload))

    wd = ChakraWatchdog(get_heartbeats, threshold=5, emitter=capture)
    wd.poll_once(now=now)
    assert events and events[0].event_type == "chakra_down"

    called: Dict[str, bool] = {}

    def repair_root() -> bool:
        called["root"] = True
        return True

    resuscitator = ChakraResuscitator({"root": repair_root}, emitter=lambda *_: None)
    caplog.set_level(logging.INFO)
    asyncio.run(resuscitator.handle_event(events[0]))

    assert called.get("root") is True
    assert "Resuscitated chakra root" in caplog.text
