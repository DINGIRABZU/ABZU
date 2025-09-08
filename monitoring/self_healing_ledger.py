from __future__ import annotations

"""Log self-healing events and persist heartbeat state."""

__version__ = "0.2.0"

import json
import time
from pathlib import Path
from typing import Callable, Dict, List

from distributed_memory import HeartbeatTimestampStore

__all__ = ["SelfHealingLedger"]


class SelfHealingLedger:
    """Record component recovery steps and heartbeat timestamps."""

    def __init__(
        self,
        store: HeartbeatTimestampStore | None = None,
        *,
        log_path: str | Path = "logs/self_healing.json",
        on_event: Callable[[Dict[str, object]], None] | None = None,
    ) -> None:
        self.store = store or HeartbeatTimestampStore(path="heartbeat_state.json")
        self.log_path = Path(log_path)
        self._beats: Dict[str, float] = {}
        self._on_event = on_event

    def recover_state(self) -> Dict[str, float]:
        """Load persisted heartbeat timestamps and return them."""

        self._beats = self.store.load()
        return dict(self._beats)

    # ------------------------------------------------------------------
    def _write(self, entry: Dict[str, object]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry))
            fh.write("\n")
        if self._on_event:
            try:
                self._on_event(entry)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def component_down(self, component: str, *, timestamp: float | None = None) -> None:
        entry = {
            "event": "component_down",
            "component": component,
            "timestamp": timestamp or time.time(),
        }
        self._write(entry)

    # ------------------------------------------------------------------
    def repair_attempt(self, component: str, *, timestamp: float | None = None) -> None:
        entry = {
            "event": "repair_attempt",
            "component": component,
            "timestamp": timestamp or time.time(),
        }
        self._write(entry)

    # ------------------------------------------------------------------
    def final_status(
        self, component: str, status: str, *, timestamp: float | None = None
    ) -> None:
        ts = timestamp or time.time()
        entry = {
            "event": "final_status",
            "component": component,
            "status": status,
            "timestamp": ts,
        }
        self._write(entry)
        self._beats[component] = ts
        self.store.update(component, ts)

    # ------------------------------------------------------------------
    def read_entries(self) -> List[Dict[str, object]]:
        """Return all ledger events from ``log_path``."""

        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    # ------------------------------------------------------------------
    def active_repairs(self) -> Dict[str, float]:
        """Return components currently undergoing repair."""

        active: Dict[str, float] = {}
        for entry in self.read_entries():
            comp = entry.get("component")
            event = entry.get("event")
            ts = float(entry.get("timestamp", 0.0))
            if event == "final_status":
                active.pop(comp, None)
            elif event in {"component_down", "repair_attempt"} and comp:
                active[comp] = ts
        return active
