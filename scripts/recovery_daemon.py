from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from razar import ai_invoker, recovery_manager, health_checks
from razar.bootstrap_utils import LOGS_DIR, STATE_FILE

__version__ = "0.2.0"

LOGGER = logging.getLogger(__name__)

INVOCATION_LOG_PATH = LOGS_DIR / "razar_ai_invocations.json"


def _log_ai_invocation(component: str, attempt: int, error: str, patched: bool) -> None:
    """Append AI handover attempt details to :data:`INVOCATION_LOG_PATH`."""
    entry = {
        "component": component,
        "attempt": attempt,
        "error": error,
        "patched": patched,
        "timestamp": time.time(),
    }
    records: List[Dict[str, Any]] = []
    if INVOCATION_LOG_PATH.exists():
        try:
            records = json.loads(INVOCATION_LOG_PATH.read_text())
            if not isinstance(records, list):
                records = []
        except json.JSONDecodeError:
            records = []
    records.append(entry)
    INVOCATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVOCATION_LOG_PATH.write_text(json.dumps(records, indent=2))


def _load_events() -> List[Dict[str, Any]]:
    if not STATE_FILE.exists():
        return []
    try:
        data = json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return []
    return data.get("events", [])


def _handle_event(event: Dict[str, Any], *, max_attempts: int = 3) -> None:
    if event.get("step") != "launch" or event.get("status") != "fail":
        return
    component = event.get("component", "")
    error = event.get("error", "")
    LOGGER.info("Attempting recovery for %s", component)
    recovery_manager.request_shutdown(component)
    for attempt in range(1, max_attempts + 1):
        patched = ai_invoker.handover(component, error)
        _log_ai_invocation(component, attempt, error, patched)
        if not patched:
            continue
        recovery_manager.resume(component)
        if health_checks.run(component):
            LOGGER.info("Component %s recovered", component)
            return
        LOGGER.error("Post-patch health check failed for %s", component)
        recovery_manager.request_shutdown(component)
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
