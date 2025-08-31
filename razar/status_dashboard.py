from __future__ import annotations

__version__ = "0.2.2"

"""Simple CLI dashboard reporting boot status and quarantine information.

The dashboard reads component priority definitions from
``docs/component_priorities.yaml`` and combines them with the last successful
component stored in ``logs/razar_state.json``. Quarantined components are
identified using :mod:`razar.quarantine_manager`.

Running ``python -m razar.status_dashboard`` prints a table summarising the
current boot attempt, component priority/criticality and links to the
quarantine log and boot history.
"""

from pathlib import Path
import json
import re
import sys
from typing import Dict, List

import yaml

from razar import quarantine_manager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = PROJECT_ROOT / "logs" / "razar_state.json"
PRIORITY_FILE = PROJECT_ROOT / "docs" / "component_priorities.yaml"
BOOT_LOG = Path(__file__).with_name("boot_orchestrator.log")


def _load_priorities() -> Dict[str, Dict[str, str]]:
    """Return component priority mappings."""

    if PRIORITY_FILE.exists():
        data = yaml.safe_load(PRIORITY_FILE.read_text())
        if isinstance(data, dict):
            return {str(k): dict(v) for k, v in data.items()}
    return {}


def _last_component() -> str | None:
    """Return the last successfully started component."""

    try:
        state = json.loads(STATE_FILE.read_text())
        return state.get("last_component") or None
    except Exception:
        return None


def _current_boot_attempt() -> int:
    """Extract the current boot attempt from the boot log.

    The last line containing the pattern "Attempt <n>" is used. ``1`` is
    returned when no attempts are recorded.
    """

    try:
        text = BOOT_LOG.read_text().splitlines()
        for line in reversed(text):
            match = re.search(r"Attempt (\d+)", line)
            if match:
                return int(match.group(1))
        return 1 if text else 0
    except Exception:
        return 0


def _component_statuses() -> List[Dict[str, str]]:
    """Compile component statuses with priority and criticality."""

    priorities = _load_priorities()
    last = _last_component()
    reached = False
    statuses: List[Dict[str, str]] = []
    for name, meta in priorities.items():
        status = "pending"
        if quarantine_manager.is_quarantined(name):
            status = "quarantined"
        elif name == last:
            status = "running"
            reached = True
        elif not reached and last:
            status = "running"
        statuses.append(
            {
                "name": name,
                "priority": meta.get("priority", ""),
                "criticality": meta.get("criticality", ""),
                "status": status,
            }
        )
        if name == last:
            reached = True
    return statuses


def render_dashboard() -> str:
    """Return a formatted dashboard string."""

    lines = [f"Current boot attempt: {_current_boot_attempt()}", ""]
    headers = f"{'Component':<20} {'Priority':<8} {'Criticality':<12} {'Status':<12}"
    lines.append(headers)
    lines.append("-" * len(headers))
    for item in _component_statuses():
        line = (
            f"{item['name']:<20} {item['priority']:<8} "
            f"{item['criticality']:<12} {item['status']:<12}"
        )
        lines.append(line)
    lines.append("")
    lines.append(
        f"Quarantine log: {quarantine_manager.LOG_FILE.relative_to(PROJECT_ROOT)}"
    )
    lines.append(f"Boot history: {BOOT_LOG.relative_to(PROJECT_ROOT)}")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    """CLI entry point printing the dashboard."""

    sys.stdout.write(render_dashboard() + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI usage
    raise SystemExit(main(sys.argv[1:]))
