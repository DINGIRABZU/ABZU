from __future__ import annotations

"""Utilities for quarantining failing components.

Components that fail during boot are moved to the top-level ``quarantine``
folder and logged in ``docs/quarantine_log.md``. Remote agents may submit
additional diagnostic information which is recorded alongside quarantine
events. Once a patch is verified, components can be reactivated either
manually or automatically.
"""

from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Any, Dict

from .issue_analyzer import IssueType

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
            "Failed modules are moved to the `quarantine/` directory and "
            "recorded below with their issue type and suggested fix.\n\n"
            "## Restoring modules\n\n"
            "To reinstate a module once it is fixed:\n\n"
            "1. Return the file from the `quarantine/` directory to its "
            "original location.\n"
            "2. Append a `resolved` entry in this log with any relevant notes.\n\n"
            "| Timestamp (UTC) | Module | Issue Type | Suggested Fix |\n"
            "|-----------------|--------|------------|---------------|\n"
        )


def _append_log(name: str, issue_type: str, fix: str) -> None:
    ts = datetime.utcnow().isoformat()
    with LOG_FILE.open("a") as fh:
        fh.write(f"| {ts} | {name} | {issue_type} | {fix} |\n")


def is_quarantined(name: str) -> bool:
    """Return ``True`` if ``name`` is quarantined."""
    _init_paths()
    return any(
        [
            (QUARANTINE_DIR / f"{name}.json").exists(),
            (QUARANTINE_DIR / name).exists(),
        ]
    )


def quarantine_component(
    component: Dict[str, Any],
    issue_type: IssueType,
    fix: str,
    diagnostics: Dict[str, Any] | None = None,
) -> None:
    """Move ``component`` metadata to quarantine and record ``issue_type``."""

    _init_paths()
    name = component.get("name", "unknown")
    with (QUARANTINE_DIR / f"{name}.json").open("w") as fh:
        json.dump(component, fh, indent=2)
    _append_log(name, issue_type.value, fix)
    if diagnostics:
        record_diagnostics(name, diagnostics)


def quarantine_module(module_path: str | Path, issue_type: IssueType, fix: str) -> Path:
    """Move ``module_path`` to :data:`QUARANTINE_DIR` and log ``issue_type``."""

    _init_paths()
    src = Path(module_path)
    if not src.exists():
        raise FileNotFoundError(src)
    target = QUARANTINE_DIR / src.name
    shutil.move(str(src), target)
    _append_log(src.name, issue_type.value, fix)
    return target


def resolve_component(name: str, note: str | None = None) -> None:
    """Remove ``name`` from quarantine and append a log entry."""
    _init_paths()
    target_json = QUARANTINE_DIR / f"{name}.json"
    target_file = QUARANTINE_DIR / name
    for target in (target_json, target_file):
        if target.exists():
            target.unlink()
    _append_log(name, "resolved", note or "")


def record_diagnostics(name: str, data: Dict[str, Any]) -> None:
    """Append diagnostic ``data`` for ``name`` to the log.

    ``data`` is serialized to JSON so it can be embedded in the Markdown log
    table. Remote code agents may call this function directly to submit
    information about a failure.
    """

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
    """Reinstate ``name`` after a verified patch.

    Parameters
    ----------
    name:
        Component to reactivate.
    verified:
        ``True`` when a patch has been verified. ``False`` raises a
        :class:`ValueError`.
    automated:
        Set to ``True`` if the reactivation was triggered automatically.
    note:
        Optional additional context to include in the log entry.
    """

    if not verified:
        raise ValueError("Patch must be verified before reactivation")

    _init_paths()
    target = QUARANTINE_DIR / f"{name}.json"
    if target.exists():
        target.unlink()
    mode = "auto" if automated else "manual"
    detail = f"{mode}{': ' + note if note else ''}"
    _append_log(name, "reactivated", detail)
