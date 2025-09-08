from __future__ import annotations

import pathlib
import sys
from types import ModuleType

pkg = ModuleType("connectors")
pkg.__path__ = [str(pathlib.Path("connectors").resolve())]
sys.modules.setdefault("connectors", pkg)

import connectors.signal_bus as signal_bus


def test_publish_subscribe() -> None:
    received: list[dict] = []
    unsub = signal_bus.subscribe("root", received.append)
    signal_bus.publish("root", {"msg": "hi"})
    unsub()
    assert received == [{"msg": "hi", "chakra": "root"}]
