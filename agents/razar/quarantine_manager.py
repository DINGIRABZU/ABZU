from __future__ import annotations

"""Utilities for quarantining failing components.

Components that fail during runtime are moved to the repository‑level
``quarantine`` directory and a human‑readable entry is appended to
``docs/quarantine_log.md``.  Remote code agents may also submit diagnostic
information which is recorded in the same Markdown log.  A component remains
quarantined until it is explicitly resolved or reactivated.
"""

from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Any, Dict, List

from agents import emit_event

# Determine project root from the module location (``agents/razar`` -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUARANTINE_DIR = PROJECT_ROOT / "quarantine"
LOG_FILE = PROJECT_ROOT / "docs" / "quarantine_log.md"

# Public symbols re-exported for convenience
__all__ = [
    "quarantine_component",
    "quarantine_module",
    "resolve_component",
    "record_diagnostics",
    "record_patch",
    "reactivate_component",
    "is_quarantined",
]


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


def _metadata_path(name: str) -> Path:
    return QUARANTINE_DIR / f"{name}.json"


def _load_metadata(name: str) -> Dict[str, Any]:
    path = _metadata_path(name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_metadata(name: str, data: Dict[str, Any]) -> None:
    with _metadata_path(name).open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


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
    """Move ``component`` metadata to quarantine and record ``reason``.

    ``attempts`` is incremented each time the component is quarantined. A
    ``patches_applied`` list tracks patch identifiers added via
    :func:`record_patch`.
    """

    _init_paths()
    name = component.get("name", "unknown")
    existing = _load_metadata(name)
    data: Dict[str, Any] = {
        **component,
        "reason": reason,
        "attempts": int(existing.get("attempts", 0)) + 1,
        "patches_applied": existing.get("patches_applied", []),
    }
    _write_metadata(name, data)
    _append_log(name, "quarantined", reason)
    if diagnostics:
        record_diagnostics(name, diagnostics)
    emit_event("razar", "component_quarantined", {"name": name, "reason": reason})


def quarantine_module(path: str | Path, reason: str) -> Path:
    """Move the file at ``path`` to :data:`QUARANTINE_DIR` and log ``reason``."""

    _init_paths()
    src = Path(path)
    if not src.exists():  # pragma: no cover - defensive
        raise FileNotFoundError(src)
    target = QUARANTINE_DIR / src.name
    shutil.move(str(src), target)
    metadata = {
        "name": src.name,
        "original_path": str(src),
        "reason": reason,
        "quarantined_at": datetime.utcnow().isoformat(),
    }
    _write_metadata(src.name, metadata)
    _append_log(src.name, "quarantined", f"{reason}; moved from {src}")
    emit_event(
        "razar",
        "module_quarantined",
        {"module": src.name, "reason": reason},
    )
    return target


def resolve_component(name: str, note: str | None = None) -> None:
    """Remove ``name`` from quarantine and append a log entry."""

    _init_paths()
    targets = [QUARANTINE_DIR / f"{name}.json", QUARANTINE_DIR / name]
    for target in targets:
        if target.exists():
            target.unlink()
    _append_log(name, "resolved", note or "")
    emit_event("razar", "component_resolved", {"name": name, "note": note})


def record_diagnostics(name: str, data: Dict[str, Any]) -> None:
    """Append diagnostic ``data`` for ``name`` to the log."""

    _init_paths()
    serialized = json.dumps(data, sort_keys=True)
    _append_log(name, "diagnostic", serialized)
    emit_event("razar", "diagnostic_recorded", {"name": name, "data": data})


def record_patch(name: str, patch: str) -> None:
    """Record that ``patch`` was applied to ``name``."""

    _init_paths()
    data = _load_metadata(name)
    patches: List[str] = list(data.get("patches_applied", []))
    patches.append(patch)
    data["patches_applied"] = patches
    _write_metadata(name, data)
    _append_log(name, "patch", patch)
    emit_event("razar", "patch_recorded", {"name": name, "patch": patch})


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
    emit_event(
        "razar",
        "component_reactivated",
        {"name": name, "mode": mode, "note": note},
    )
