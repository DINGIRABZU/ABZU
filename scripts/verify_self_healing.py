#!/usr/bin/env python3
"""Verify self-healing health checks."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

__version__ = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_INDEX = PROJECT_ROOT / "docs" / "INDEX.md"
MANIFEST = PROJECT_ROOT / "docs" / "self_healing_manifesto.md"
SELF_HEAL_LOG = PROJECT_ROOT / "logs" / "self_heal.jsonl"
QUARANTINE_DIR = PROJECT_ROOT / "quarantine"


def _manifest_listed(index: Path = DOCS_INDEX, manifest: Path = MANIFEST) -> bool:
    """Return True if manifest is referenced in docs index."""
    if not index.exists() or not manifest.exists():
        return False
    return manifest.name in index.read_text(encoding="utf-8")


def _recent_successful_cycles(
    log: Path = SELF_HEAL_LOG, *, max_age_hours: int = 24
) -> bool:
    """Return True if log contains a recent successful entry."""
    if not log.exists():
        return False
    threshold = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        status = data.get("status")
        ts = data.get("timestamp") or data.get("time") or data.get("ts")
        if status != "success" or not ts:
            continue
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= threshold:
            return True
    return False


def _quarantine_fresh(
    directory: Path = QUARANTINE_DIR, *, max_age_hours: int = 24
) -> bool:
    """Return True if no quarantined component exceeds threshold."""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=max_age_hours)
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False
        ts = data.get("quarantined_at")
        if not ts:
            return False
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return False
        if when < threshold:
            return False
    return True


def verify_self_healing(
    *, max_quarantine_hours: int = 24, max_cycle_hours: int = 24
) -> int:
    """Exit non-zero if self-healing invariants are violated."""
    errors: list[str] = []
    if not _manifest_listed():
        errors.append("docs/self_healing_manifesto.md missing from docs/INDEX.md")
    if not _recent_successful_cycles(max_age_hours=max_cycle_hours):
        errors.append(
            f"no successful self-heal cycles in last {max_cycle_hours}h"
        )
    if not _quarantine_fresh(max_age_hours=max_quarantine_hours):
        errors.append(
            "quarantined component exceeds age threshold"
            f" ({max_quarantine_hours}h)"
        )
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("verify_self_healing: all checks passed")
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-quarantine-hours",
        type=int,
        default=24,
        help="Maximum allowed quarantine age in hours",
    )
    parser.add_argument(
        "--max-cycle-hours",
        type=int,
        default=24,
        help="Maximum age of successful self-heal cycle in hours",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return verify_self_healing(
        max_quarantine_hours=args.max_quarantine_hours,
        max_cycle_hours=args.max_cycle_hours,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
