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
    heartbeats: list[dict] = []
    alerts: list[dict] = []
    unsub_hb = signal_bus.subscribe("test:heartbeat", heartbeats.append)
    unsub_alert = signal_bus.subscribe("test:alert", alerts.append)
    hb = ConnectorHeartbeat("test", interval=0.01, miss_threshold=2)
    hb.start()
    time.sleep(0.035)
    hb.pause()
    time.sleep(0.05)
    hb.stop()
    unsub_hb()
    unsub_alert()
    cycles = [p["cycle"] for p in heartbeats]
    assert len(cycles) >= 2 and cycles[0] == 1 and cycles[1] == 2
    assert alerts and alerts[0]["channel"] == "test"
