from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, List, Mapping

from citadel.event_producer import Event

import agents.event_bus as event_bus
import agents.nazarick.chakra_observer as chakra_observer
from agents.nazarick.chakra_resuscitator import ChakraResuscitator
import monitoring.chakra_watchdog as chakra_watchdog
from monitoring.chakra_watchdog import ChakraWatchdog


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


def test_delayed_heartbeat_emits_target_agent_and_observer_repairs(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(event_bus, "emit_event", lambda *_, **__: None)
    monkeypatch.setattr(event_bus, "subscribe", lambda *_, **__: None)

    now = time.time()
    heartbeats = {"root": now - 10}

    def get_heartbeats() -> Mapping[str, float]:
        return heartbeats

    events: List[Event] = []

    def capture(actor: str, action: str, payload: Dict[str, float | str]) -> None:
        events.append(Event(agent_id=actor, event_type=action, payload=payload))

    monkeypatch.setattr(chakra_watchdog, "CHAKRA_TO_AGENT", {"root": "test_agent"})
    wd = ChakraWatchdog(get_heartbeats, threshold=5, emitter=capture)
    wd.poll_once(now=now)

    assert events and events[0].payload.get("target_agent") == "test_agent"

    registry = tmp_path / "agent_registry.json"
    registry.write_text(
        json.dumps({"agents": [{"id": "test_agent", "chakra": "root"}]})
    )
    monkeypatch.setattr(chakra_observer, "REGISTRY_FILE", registry)

    called: Dict[str, bool] = {}

    def repair_root() -> bool:
        called["root"] = True
        return True

    observer = chakra_observer.NazarickChakraObserver(
        "test_agent", repair_root, emitter=lambda *_: None
    )
    asyncio.run(observer.handle_event(events[0]))

    assert called.get("root") is True
