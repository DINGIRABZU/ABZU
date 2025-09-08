from __future__ import annotations

import pathlib
import sys
import time
from types import ModuleType

pkg = ModuleType("connectors")
pkg.__path__ = [str(pathlib.Path("connectors").resolve())]
sys.modules.setdefault("connectors", pkg)

import connectors.signal_bus as signal_bus
from connectors.base import ConnectorHeartbeat


def test_alert_emitted_on_missed_heartbeats() -> None:
    events: list[dict] = []
    unsub = signal_bus.subscribe("test:alert", lambda p: events.append(p))
    hb = ConnectorHeartbeat("test", interval=0.01, miss_threshold=2)
    hb.start()
    time.sleep(0.03)
    hb.pause()
    time.sleep(0.05)
    hb.stop()
    unsub()
    assert events and events[0]["channel"] == "test"
