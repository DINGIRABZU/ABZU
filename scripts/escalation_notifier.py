"""Monitor logs for recurring errors and escalate via operator command."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable, Tuple

import requests

__version__ = "0.1.0"

DEFAULT_LOG = Path("logs") / "razar_mission.log"
OPERATOR_URL = "http://localhost:8000/operator/command"
ESCALATION_LOG = Path("logs") / "operator_escalations.jsonl"


def _find_recurring_errors(
    lines: Iterable[str], threshold: int
) -> list[Tuple[str, int]]:
    """Return error messages occurring at least ``threshold`` times."""

    pattern = re.compile("error", re.IGNORECASE)
    counts: Counter[str] = Counter()
    for line in lines:
        if pattern.search(line):
            counts[line.strip()] += 1
    return [(msg, cnt) for msg, cnt in counts.items() if cnt >= threshold]


def _notify(message: str) -> bool:
    """Send ``message`` to the operator command endpoint."""

    payload = {"operator": "overlord", "agent": "crown", "command": message}
    try:
        requests.post(OPERATOR_URL, json=payload, timeout=5)
    except Exception:
        return False
    return True


def escalate(errors: list[Tuple[str, int]]) -> None:
    """Record ``errors`` and notify the operator."""

    ESCALATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    for message, count in errors:
        notified = _notify(message)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": message,
            "count": count,
            "notified": notified,
        }
        with ESCALATION_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()

    if not args.log.exists():
        return 0
    lines = args.log.read_text(encoding="utf-8").splitlines()
    errors = _find_recurring_errors(lines, args.threshold)
    if errors:
        escalate(errors)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
