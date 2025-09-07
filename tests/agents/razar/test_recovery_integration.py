"""Integration test for RecoveryManager and Nazarick ChakraResuscitator."""

from __future__ import annotations

from pathlib import Path
import queue
from typing import Dict, Iterator, List, Tuple

from agents.nazarick.chakra_resuscitator import ChakraResuscitator
from agents.razar.lifecycle_bus import Issue
from agents.razar.recovery_manager import RecoveryManager


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
        self.bus = bus
        self.state_dir = state_dir

    def pause_system(self) -> None:  # pragma: no cover - noop
        pass

    def resume_system(self) -> None:  # pragma: no cover - noop
        pass

    def apply_fixes(self, module: str) -> None:  # pragma: no cover - noop
        pass

    def restart_module(self, module: str) -> None:  # pragma: no cover - noop
        pass

    def restore_state(
        self, module: str, state: Dict[str, object]
    ) -> None:  # pragma: no cover
        pass


def test_component_down_triggers_resuscitation(tmp_path) -> None:
    bus = DummyBus()
    called: Dict[str, bool] = {}

    def repair_root() -> bool:
        called["root"] = True
        return True

    resuscitator = ChakraResuscitator(
        {"root": repair_root}, bus=bus, emitter=lambda *_: None
    )
    manager = DummyRecoveryManager(bus, tmp_path)

    manager.recover("root", {})
    resuscitator.run_bus(limit=1)

    assert called.get("root") is True
    assert ("root", "repaired") in bus.statuses
