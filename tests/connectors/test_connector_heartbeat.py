"""Tests for the :class:`ConnectorHeartbeat` mixin."""

import importlib
import pathlib
import sys
import time
from types import ModuleType
from typing import Any, Callable, Dict

pkg = ModuleType("connectors")
pkg.__path__ = [str(pathlib.Path("connectors").resolve())]
sys.modules.setdefault("connectors", pkg)

connector_base = importlib.import_module("connectors.base")
ConnectorHeartbeat = connector_base.ConnectorHeartbeat


def test_alert_emitted_on_missed_heartbeats(monkeypatch: Any) -> None:
    """Heartbeat alerts are published after consecutive misses."""
    events: list[tuple[str, Dict[str, Any]]] = []
    subs: Dict[str, list[Callable[[Dict[str, Any]], None]]] = {}

    def fake_publish(chakra: str, payload: Dict[str, Any]) -> None:
        for cb in subs.get(chakra, []):
            cb(payload)
        events.append((chakra, payload))

    def fake_subscribe(
        chakra: str, callback: Callable[[Dict[str, Any]], None]
    ) -> Callable[[], None]:
        subs.setdefault(chakra, []).append(callback)

        def _unsub() -> None:
            subs[chakra].remove(callback)

        return _unsub

    monkeypatch.setattr(connector_base, "publish", fake_publish)
    monkeypatch.setattr(connector_base, "subscribe", fake_subscribe)

    hb = ConnectorHeartbeat("test", interval=0.01, miss_threshold=2)
    hb.start()
    time.sleep(0.03)
    hb.pause()  # stop sending heartbeats
    time.sleep(0.05)
    hb.stop()

    assert any(ch == "test:alert" for ch, _ in events)
