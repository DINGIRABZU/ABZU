from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from operator_api import broadcast_event

__version__ = "0.1.0"

ESCALATION_LOG = Path("logs") / "operator_escalations.jsonl"

REQUEST_RE = re.compile(r"(?P<ts>\S+)\s+(?P<component>\S+)\s+request", re.I)
OFFLINE_RE = re.compile(r"(?P<ts>\S+)\s+(?P<component>\S+)\s+offline", re.I)


def _parse_ts(text: str) -> datetime:
    """Return ``datetime`` parsed from ISO-8601 ``text``."""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _notify(event: dict[str, object]) -> None:
    """Send ``event`` via ``broadcast_event`` and append to escalation log."""
    asyncio.run(broadcast_event({"event": "escalation", **event}))
    ESCALATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ESCALATION_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, default=str) + "\n")


def scan_logs(
    razar_log: Path, crown_log: Path, now: datetime | None = None
) -> list[dict[str, object]]:
    """Scan ``razar_log`` and ``crown_log`` for escalation conditions.

    Returns a list of escalation events that were emitted.
    """
    now = now or datetime.utcnow()
    events: list[dict[str, object]] = []

    if razar_log.exists():
        requests: dict[str, list[datetime]] = {}
        for line in razar_log.read_text().splitlines():
            match = REQUEST_RE.search(line)
            if not match:
                continue
            ts = _parse_ts(match.group("ts"))
            comp = match.group("component")
            requests.setdefault(comp, []).append(ts)
        for comp, times in requests.items():
            times.sort()
            for i in range(len(times) - 2):
                if times[i + 2] - times[i] <= timedelta(minutes=10):
                    event = {
                        "component": comp,
                        "reason": "repeated_requests",
                        "timestamp": now.isoformat() + "Z",
                    }
                    _notify(event)
                    events.append(event)
                    break

    if crown_log.exists():
        for line in crown_log.read_text().splitlines():
            match = OFFLINE_RE.search(line)
            if not match:
                continue
            ts = _parse_ts(match.group("ts"))
            if now - ts > timedelta(minutes=5):
                comp = match.group("component")
                event = {
                    "component": comp,
                    "reason": "service_offline",
                    "timestamp": now.isoformat() + "Z",
                }
                _notify(event)
                events.append(event)

    return events


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor RAZAR and Crown logs for escalation conditions."
    )
    parser.add_argument(
        "--razar-log", type=Path, default=Path("logs/razar.log"), help="RAZAR log path"
    )
    parser.add_argument(
        "--crown-log",
        type=Path,
        default=Path("logs/operator.log"),
        help="Crown log path",
    )
    args = parser.parse_args()
    scan_logs(args.razar_log, args.crown_log)
