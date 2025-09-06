from __future__ import annotations

import asyncio

from citadel.event_producer import Event

from agents.nazarick.chakra_observer import NazarickChakraObserver


def test_observer_triggers_action() -> None:
    called: dict[str, bool] = {}

    def action() -> bool:
        called["heart"] = True
        return True

    observer = NazarickChakraObserver("memory_scribe", action, emitter=lambda *_: None)
    assert observer.chakra == "heart"

    event = Event(
        agent_id="chakra_watchdog",
        event_type="chakra_down",
        payload={"chakra": "heart", "target_agent": "memory_scribe"},
    )
    asyncio.run(observer.handle_event(event))
    assert called.get("heart") is True


def test_observer_ignores_other_agents() -> None:
    called: dict[str, bool] = {}

    def action() -> bool:
        called["heart"] = True
        return True

    observer = NazarickChakraObserver("memory_scribe", action, emitter=lambda *_: None)
    event = Event(
        agent_id="chakra_watchdog",
        event_type="chakra_down",
        payload={"chakra": "heart", "target_agent": "someone_else"},
    )
    asyncio.run(observer.handle_event(event))
    assert called == {}
