from __future__ import annotations

"""Structured mission logger for RAZAR components.

This module records lifecycle events for RAZAR components in a JSON lines log
stored at ``logs/razar.log``. Each entry captures:

- ``event`` – type of event such as ``start``, ``error`` or ``recovery``
- ``component`` – component name
- ``status`` – outcome or note for the event
- ``timestamp`` – ISO-8601 time in UTC
- ``details`` – optional free-form text

Utility helpers are provided for common events including component starts,
errors and recovery attempts. Additional helpers retain backward compatible
names for health checks, quarantines and patches. The log can be summarised to
find the last successful component or rendered as a chronological timeline for
debugging.
"""

from dataclasses import dataclass
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

LOG_PATH = Path("logs/razar.log")


def _ensure_log_dir() -> None:
    """Ensure the directory for ``LOG_PATH`` exists."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LogEntry:
    """Representation of a single log entry."""

    event: str
    component: str
    status: str
    timestamp: str
    details: Optional[str] = None

    @classmethod
    def from_json(cls, line: str) -> "LogEntry":
        data = json.loads(line)
        return cls(
            event=data.get("event", "info"),
            component=data["component"],
            status=data["status"],
            timestamp=data["timestamp"],
            details=data.get("details"),
        )


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log_event(
    event: str,
    component: str,
    status: str,
    details: str | None = None,
) -> None:
    """Append an event entry for ``component`` to the mission log."""

    _ensure_log_dir()
    entry = LogEntry(
        event=event,
        component=component,
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=details,
    )
    record = {k: v for k, v in entry.__dict__.items() if v is not None}
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def log_start(component: str, status: str, details: str | None = None) -> None:
    """Record that a component has started."""

    log_event("start", component, status, details)


def log_health(
    component: str, status: str, details: str | None = None
) -> None:
    """Record a health result for a component."""

    log_event("health", component, status, details)


def log_quarantine(component: str, reason: str, details: str | None = None) -> None:
    """Record that a component has been quarantined."""

    log_event("quarantine", component, reason, details)


def log_patch(component: str, patch: str, details: str | None = None) -> None:
    """Record that a patch has been applied to a component."""

    log_event("patch", component, patch, details)


def log_error(component: str, error: str, details: str | None = None) -> None:
    """Record that a component encountered an error."""

    log_event("error", component, error, details)


def log_recovery(component: str, status: str, details: str | None = None) -> None:
    """Record a recovery attempt for a component."""

    log_event("recovery", component, status, details)


# ---------------------------------------------------------------------------
# Backwards compatibility aliases
# ---------------------------------------------------------------------------

# Older helpers used different terminology. Keep them as thin wrappers so
# existing scripts continue to work.
log_launch = log_start
log_health_check = log_health


# ---------------------------------------------------------------------------
# Reading utilities
# ---------------------------------------------------------------------------

def load_events() -> List[LogEntry]:
    """Return all log entries in chronological order."""

    if not LOG_PATH.exists():
        return []

    events: List[LogEntry] = []
    with LOG_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                events.append(LogEntry.from_json(line))
            except json.JSONDecodeError:
                continue
    events.sort(key=lambda e: e.timestamp)
    return events


def summarize(event_filter: str | None = None) -> Dict[str, Optional[List[str] | str]]:
    """Return last successful component and pending components.

    When ``event_filter`` is provided only events matching the given type are
    considered.
    """

    events = load_events()
    if event_filter:
        events = [e for e in events if e.event == event_filter]

    last_success: Optional[str] = None
    last_success_time: Optional[datetime] = None
    states: Dict[str, str] = {}

    for entry in events:
        states[entry.component] = entry.status
        if entry.status.lower() == "success":
            ts = datetime.fromisoformat(entry.timestamp)
            if not last_success_time or ts > last_success_time:
                last_success_time = ts
                last_success = entry.component

    pending = sorted(
        component for component, status in states.items() if status.lower() != "success"
    )
    return {"last_success": last_success, "pending": pending}


def timeline() -> List[Dict[str, str]]:
    """Return the raw timeline as a list of dictionaries."""

    return [e.__dict__ for e in load_events()]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _cmd_log(args: argparse.Namespace) -> None:
    log_event(args.event, args.component, args.status, args.details)


def _cmd_summary(args: argparse.Namespace) -> None:
    data = summarize(event_filter=args.event)
    print(f"Last success: {data['last_success']}")
    if data["pending"]:
        print("Pending tasks:")
        for comp in data["pending"]:
            print(f"- {comp}")
    else:
        print("Pending tasks: none")


def _cmd_timeline(_: argparse.Namespace) -> None:
    for entry in timeline():
        details = f" - {entry['details']}" if entry.get("details") else ""
        print(
            f"{entry['timestamp']} {entry['event']} {entry['component']}: {entry['status']}{details}"
        )


def main() -> None:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="RAZAR mission logger")
    sub = parser.add_subparsers(dest="command")

    p_log = sub.add_parser("log", help="Record a component event")
    p_log.add_argument("component")
    p_log.add_argument("status")
    p_log.add_argument(
        "--event",
        default="info",
        help="Event type such as start, health, quarantine or patch",
    )
    p_log.add_argument("--details", help="Optional additional information")
    p_log.set_defaults(func=_cmd_log)

    p_summary = sub.add_parser("summary", help="Show mission progress")
    p_summary.add_argument("--event", help="Filter by event type")
    p_summary.set_defaults(func=_cmd_summary)

    p_timeline = sub.add_parser("timeline", help="Show event timeline")
    p_timeline.set_defaults(func=_cmd_timeline)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover - show help when no subcommand
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

