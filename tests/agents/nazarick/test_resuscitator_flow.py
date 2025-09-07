"""Integration tests for :mod:`agents.nazarick.resuscitator`."""

from __future__ import annotations

import asyncio
import threading
import time
import queue
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from agents.nazarick.resuscitator import Resuscitator
from agents.razar import lifecycle_bus
from agents.razar.recovery_manager import RecoveryManager
from agents.razar.lifecycle_bus import Issue


def test_restart_attempt_emits_success() -> None:
    """``agent_down`` events trigger restart attempts and callbacks."""

    events: List[Dict[str, object]] = []

    def emitter(event: Dict[str, object]) -> None:
        events.append(event)

    called = False

    def restart() -> bool:
        nonlocal called
        called = True
        return True

    resuscitator = Resuscitator({"alpha": restart}, emitter=emitter)
    asyncio.run(resuscitator.handle_event({"event": "agent_down", "agent": "alpha"}))

    assert called
    assert {"event": "agent_resuscitated", "agent": "alpha"} in events


class DummyBus:
    """Minimal in-memory lifecycle bus for testing."""

    def __init__(self) -> None:
        self.statuses: List[Tuple[str, str]] = []
        self._issues: "queue.Queue[Issue]" = queue.Queue()

    def report_issue(self, component: str, issue: str) -> None:
        self._issues.put(Issue(component, issue))

    def listen_for_issues(self) -> Iterator[Issue]:
        while not self._issues.empty():
            yield self._issues.get()

    def publish_status(self, component: str, status: str) -> None:
        self.statuses.append((component, status))

    def send_control(
        self, component: str, action: str
    ) -> None:  # pragma: no cover - noop
        pass


class DummyRecoveryManager(RecoveryManager):
    """RecoveryManager variant with side effects disabled."""

    def __init__(self, bus: DummyBus, state_dir: Path) -> None:
        self.bus = bus  # type: ignore[assignment]
        self.state_dir = state_dir

    def pause_system(self) -> None:  # pragma: no cover - noop
        pass

    def resume_system(self) -> None:  # pragma: no cover - noop
        pass

    def apply_fixes(self, module: str) -> None:  # pragma: no cover - noop
        pass

    def restart_module(self, module: str) -> None:  # pragma: no cover - noop
        pass

    def save_state(
        self, module: str, state: Dict[str, object]
    ) -> None:  # pragma: no cover
        pass

    def restore_state(
        self, module: str, state: Dict[str, object]
    ) -> None:  # pragma: no cover
        pass


def test_manager_waits_for_resuscitator(tmp_path: Path) -> None:
    lifecycle_bus.aioredis = None  # type: ignore[attr-defined]
    lifecycle_bus.AIOKafkaProducer = None  # type: ignore[attr-defined]
    lifecycle_bus.AIOKafkaConsumer = None  # type: ignore[attr-defined]
    bus = DummyBus()
    manager = DummyRecoveryManager(bus, tmp_path)

    def confirm() -> None:
        time.sleep(0.1)
        lifecycle_bus.publish({"event": "agent_resuscitated", "agent": "beta"})

    t = threading.Thread(target=confirm)
    t.start()
    manager.recover("beta", {})
    t.join()

    assert ("beta", "healthy") in bus.statuses
