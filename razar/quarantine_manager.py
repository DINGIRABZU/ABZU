from __future__ import annotations

"""Utilities for quarantining failing components.

Components that fail during boot are moved to the top-level ``quarantine``
folder and logged in ``docs/quarantine_log.md``.
"""

from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUARANTINE_DIR = PROJECT_ROOT / "quarantine"
LOG_FILE = PROJECT_ROOT / "docs" / "quarantine_log.md"


def _init_paths() -> None:
    """Ensure quarantine directory and log file exist."""
    QUARANTINE_DIR.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(exist_ok=True)
        LOG_FILE.write_text(
            "# Quarantine Log\n\n"
            "Failed components are moved to the `quarantine/` directory and recorded below.\n\n"
            "## Restoring components\n\n"
            "To reinstate a component once it is fixed:\n\n"
            "1. Remove its JSON file from the `quarantine/` directory.\n"
            "2. Append a `resolved` entry in this log with any relevant notes.\n\n"
            "| Timestamp (UTC) | Component | Action | Details |\n"
            "|-----------------|-----------|--------|---------|\n"
        )


def _append_log(name: str, action: str, details: str) -> None:
    ts = datetime.utcnow().isoformat()
    with LOG_FILE.open("a") as fh:
        fh.write(f"| {ts} | {name} | {action} | {details} |\n")


def is_quarantined(name: str) -> bool:
    """Return ``True`` if ``name`` is quarantined."""
    _init_paths()
    return (QUARANTINE_DIR / f"{name}.json").exists()


def quarantine_component(component: Dict[str, Any], reason: str) -> None:
    """Move ``component`` to quarantine and record ``reason``."""
    _init_paths()
    name = component.get("name", "unknown")
    with (QUARANTINE_DIR / f"{name}.json").open("w") as fh:
        json.dump(component, fh, indent=2)
    _append_log(name, "quarantined", reason)


def resolve_component(name: str, note: str | None = None) -> None:
    """Remove ``name`` from quarantine and append a log entry."""
    _init_paths()
    target = QUARANTINE_DIR / f"{name}.json"
    if target.exists():
        target.unlink()
    _append_log(name, "resolved", note or "")
