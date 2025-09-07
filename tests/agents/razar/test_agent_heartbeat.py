from __future__ import annotations

import asyncio
import pytest

from monitoring.agent_heartbeat import AgentHeartbeat
from agents.razar import lifecycle_bus


def test_missing_beat_emits_agent_down(monkeypatch) -> None:
    hb = AgentHeartbeat(agents=["alpha"], window=0.1)
    hb.beat("alpha", timestamp=0.0)
    events: list[dict[str, object]] = []

    def capture(event: dict[str, object]) -> None:
        events.append(event)

    monkeypatch.setattr(lifecycle_bus, "publish", capture)
    with pytest.raises(RuntimeError):
        hb.check_alerts(now=1.0)
    assert {"event": "agent_down", "agent": "alpha"} in events


def test_event_subscription(monkeypatch) -> None:
    hb = AgentHeartbeat(window=1.0)

    async def fake_stream():
        yield {"event": "agent_beat", "agent": "beta", "timestamp": 0.0}

    monkeypatch.setattr(lifecycle_bus, "subscribe", lambda: fake_stream())
    asyncio.run(hb.listen())
    assert "beta" in hb.heartbeats()
