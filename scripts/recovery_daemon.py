from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from razar import ai_invoker, recovery_manager
from razar.bootstrap_utils import STATE_FILE

__version__ = "0.1.0"

LOGGER = logging.getLogger(__name__)


def _load_events() -> List[Dict[str, Any]]:
    if not STATE_FILE.exists():
        return []
    try:
        data = json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return []
    return data.get("events", [])


def _handle_event(event: Dict[str, Any]) -> None:
    if event.get("step") != "launch" or event.get("status") != "fail":
        return
    component = event.get("component", "")
    error = event.get("error", "")
    LOGGER.info("Attempting recovery for %s", component)
    recovery_manager.request_shutdown(component)
    patched = ai_invoker.handover(component, error)
    if patched:
        recovery_manager.resume(component)
        LOGGER.info("Component %s recovered", component)
    else:
        LOGGER.warning("Automatic recovery failed for %s", component)


def monitor(interval: float = 1.0) -> None:
    logging.basicConfig(level=logging.INFO)
    last = 0
    while True:
        events = _load_events()
        new_events = events[last:]
        for event in new_events:
            _handle_event(event)
        last = len(events)
        time.sleep(interval)


def main() -> None:
    monitor()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
