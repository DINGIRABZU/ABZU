#!/usr/bin/env python3
"""Check onboarding doc summaries stay in sync with file hashes."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIRM = ROOT / "onboarding_confirm.yml"
REQUIRED_FIELDS = ("purpose", "scope", "key_rules", "insight")
__version__ = "0.2.0"


def sha256(path: Path) -> str:
    """Return the SHA256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Exit non-zero if any document hash or summary is outdated or missing."""
    if not CONFIRM.exists():
        print(
            "onboarding_confirm.yml missing. "
            "Run scripts/confirm_reading.py after reviewing key documents.",
            file=sys.stderr,
        )
        return 1

    try:
        data = yaml.safe_load(CONFIRM.read_text()) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - parse errors are rare
        print(f"Failed to parse {CONFIRM}: {exc}", file=sys.stderr)
        return 1

    docs: dict[str, object] = data.get("documents", {})
    if not docs:
        print("onboarding_confirm.yml has no document entries", file=sys.stderr)
        return 1

    missing_files: list[str] = []
    missing_fields: list[str] = []
    mismatched: list[str] = []
    for rel_path, info in docs.items():
        path = ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue
        if isinstance(info, dict):
            sha = info.get("sha256")
            summary = info.get("summary") or {}
            if not sha or any(not summary.get(f) for f in REQUIRED_FIELDS):
                missing_fields.append(rel_path)
                continue
        else:  # backward compatibility with plain hash entries
            sha = info
        if sha256(path) != sha:
            mismatched.append(rel_path)

    if missing_files or missing_fields or mismatched:
        for p in missing_files:
            print(f"Missing document: {p}", file=sys.stderr)
        for p in missing_fields:
            print(f"Missing sha256 or summary fields for: {p}", file=sys.stderr)
        for p in mismatched:
            print(f"Hash mismatch: {p}", file=sys.stderr)
        print(
            "Update onboarding_confirm.yml after re-reading changed files.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
