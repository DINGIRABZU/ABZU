from __future__ import annotations

"""Utilities for quarantining failing components.

Components that fail during runtime are moved to the repository-level
``quarantine`` directory and recorded in ``docs/quarantine_log.md``. Remote code
agents may also submit diagnostic information which is appended to the log. A
component remains quarantined until it is explicitly resolved or reactivated.
"""

from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Any, Dict

# Determine project root from the module location (``agents/razar`` -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUARANTINE_DIR = PROJECT_ROOT / "quarantine"
LOG_FILE = PROJECT_ROOT / "docs" / "quarantine_log.md"


def _init_paths() -> None:
    """Ensure quarantine directory and log file exist."""

    QUARANTINE_DIR.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(exist_ok=True)
        header = (
            "# Quarantine Log\n\n"
            "Failed components are moved to the `quarantine/` directory "
            "and recorded below.\n\n"
            "## Restoring components\n\n"
            "To reinstate a component once it is fixed:\n\n"
            "1. Remove its JSON file from the `quarantine/` directory.\n"
            "2. Append a `resolved` entry in this log with any relevant notes.\n\n"
            "| Timestamp (UTC) | Component | Action | Details |\n"
            "|-----------------|-----------|--------|---------|\n"
        )
        LOG_FILE.write_text(header, encoding="utf-8")


def _append_log(name: str, action: str, details: str) -> None:
    ts = datetime.utcnow().isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"| {ts} | {name} | {action} | {details} |\n")


def is_quarantined(name: str) -> bool:
    """Return ``True`` if ``name`` is quarantined."""

    _init_paths()
    return (QUARANTINE_DIR / f"{name}.json").exists() or (
        QUARANTINE_DIR / name
    ).exists()


def quarantine_component(
    component: Dict[str, Any],
    reason: str,
    diagnostics: Dict[str, Any] | None = None,
) -> None:
    """Move ``component`` metadata to quarantine and record ``reason``."""

    _init_paths()
    name = component.get("name", "unknown")
    with (QUARANTINE_DIR / f"{name}.json").open("w", encoding="utf-8") as fh:
        json.dump(component, fh, indent=2)
    _append_log(name, "quarantined", reason)
    if diagnostics:
        record_diagnostics(name, diagnostics)


def quarantine_module(path: str | Path, reason: str) -> Path:
    """Move the file at ``path`` to :data:`QUARANTINE_DIR` and log ``reason``."""

    _init_paths()
    src = Path(path)
    if not src.exists():  # pragma: no cover - defensive
        raise FileNotFoundError(src)
    target = QUARANTINE_DIR / src.name
    shutil.move(str(src), target)
    _append_log(src.name, "quarantined", reason)
    return target


def resolve_component(name: str, note: str | None = None) -> None:
    """Remove ``name`` from quarantine and append a log entry."""

    _init_paths()
    targets = [QUARANTINE_DIR / f"{name}.json", QUARANTINE_DIR / name]
    for target in targets:
        if target.exists():
            target.unlink()
    _append_log(name, "resolved", note or "")


def record_diagnostics(name: str, data: Dict[str, Any]) -> None:
    """Append diagnostic ``data`` for ``name`` to the log."""

    _init_paths()
    serialized = json.dumps(data, sort_keys=True)
    _append_log(name, "diagnostic", serialized)


def reactivate_component(
    name: str,
    *,
    verified: bool,
    automated: bool = False,
    note: str | None = None,
) -> None:
    """Reinstate ``name`` after a verified patch."""

    if not verified:
        raise ValueError("Patch must be verified before reactivation")

    _init_paths()
    targets = [QUARANTINE_DIR / f"{name}.json", QUARANTINE_DIR / name]
    for target in targets:
        if target.exists():
            target.unlink()
    mode = "auto" if automated else "manual"
    detail = f"{mode}{': ' + note if note else ''}"
    _append_log(name, "reactivated", detail)
