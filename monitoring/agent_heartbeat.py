"""Track agent heartbeat events and detect outages."""

from __future__ import annotations

import time
from typing import Dict, Iterable, List

from agents.razar import lifecycle_bus

__version__ = "0.1.1"


class AgentHeartbeat:
    """Track last heartbeat per agent with optional alerting."""

    def __init__(
        self, agents: Iterable[str] | None = None, *, window: float = 5.0
    ) -> None:
        self.window = window
        self._agents = set(agents or [])
        self._beats: Dict[str, float] = {}

    async def listen(self) -> None:
        """Subscribe to lifecycle events and update timestamps.

        After processing each beat the method invokes :meth:`check_alerts` to
        publish ``agent_down`` events for agents that have missed their
        heartbeat window.  Any resulting :class:`RuntimeError` is suppressed so
        that monitoring can continue.
        """

        async for event in lifecycle_bus.subscribe():
            if event.get("event") != "agent_beat":
                continue
            agent = event.get("agent")
            if agent:
                ts = float(event.get("timestamp", time.time()))
                self.beat(str(agent), ts)
            try:
                self.check_alerts()
            except RuntimeError:
                # ``check_alerts`` raises if any agents are missing.  When
                # running as a background listener we simply emit the
                # ``agent_down`` events and keep listening.
                pass

    def beat(self, agent: str, timestamp: float | None = None) -> None:
        """Record a heartbeat for ``agent`` at ``timestamp``."""

        ts = timestamp or time.time()
        self._agents.add(agent)
        self._beats[agent] = ts

    def heartbeats(self) -> Dict[str, float]:
        """Return mapping of agents to their last heartbeat."""

        return dict(self._beats)

    def pending(self, *, now: float | None = None) -> List[str]:
        """Return agents missing a beat beyond the window."""

        current = now or time.time()
        missing: List[str] = []
        for agent in self._agents:
            ts = self._beats.get(agent, 0.0)
            if current - ts > self.window:
                missing.append(agent)
        return missing

    def check_alerts(self, *, now: float | None = None) -> None:
        """Emit ``agent_down`` events for agents missing beats."""

        missing = self.pending(now=now)
        for agent in missing:
            lifecycle_bus.publish({"event": "agent_down", "agent": agent})
        if missing:
            raise RuntimeError(f"Missing heartbeats: {', '.join(missing)}")


__all__ = ["AgentHeartbeat"]
