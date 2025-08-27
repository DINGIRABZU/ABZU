from __future__ import annotations

"""Structured mission logger for RAZAR.

This module records component status updates in ``logs/razar.log`` with
three fields: ``component``, ``status`` and an ISO-8601 ``timestamp``. It
also provides a summary command that reports the last successful component
and any components that remain pending.
"""

from dataclasses import dataclass
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

LOG_PATH = Path("logs/razar.log")


def _ensure_log_dir() -> None:
    """Create the log directory if it does not exist."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LogEntry:
    component: str
    status: str
    timestamp: str

    @classmethod
    def from_json(cls, line: str) -> "LogEntry":
        data = json.loads(line)
        return cls(
            component=data["component"],
            status=data["status"],
            timestamp=data["timestamp"],
        )


def log_event(component: str, status: str) -> None:
    """Append a status update for ``component``."""
    _ensure_log_dir()
    entry = LogEntry(
        component=component,
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.__dict__) + "\n")


def summarize() -> Dict[str, Optional[List[str] | str]]:
    """Return last successful component and pending components.

    Returns a dictionary with ``last_success`` and ``pending`` keys.
    ``pending`` is a sorted list of components whose most recent status is
    not ``success``.
    """
    if not LOG_PATH.exists():
        return {"last_success": None, "pending": []}

    last_success: Optional[str] = None
    last_success_time: Optional[datetime] = None
    states: Dict[str, str] = {}

    with LOG_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = LogEntry.from_json(line)
            except json.JSONDecodeError:
                continue
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


def _cmd_log(args: argparse.Namespace) -> None:
    log_event(args.component, args.status)


def _cmd_summary(_: argparse.Namespace) -> None:
    data = summarize()
    print(f"Last success: {data['last_success']}")
    if data["pending"]:
        print("Pending tasks:")
        for comp in data["pending"]:
            print(f"- {comp}")
    else:
        print("Pending tasks: none")


def main() -> None:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="RAZAR mission logger")
    sub = parser.add_subparsers(dest="command")

    p_log = sub.add_parser("log", help="Record a component status")
    p_log.add_argument("component")
    p_log.add_argument("status")
    p_log.set_defaults(func=_cmd_log)

    p_summary = sub.add_parser("summary", help="Show mission progress")
    p_summary.set_defaults(func=_cmd_summary)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
