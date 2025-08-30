"""Ensure protected documents have up-to-date hashes and summaries."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KEY_DOCS = ROOT / "docs" / "KEY_DOCUMENTS.md"
CONFIRM = ROOT / "onboarding_confirm.yml"
__version__ = "0.1.0"


def sha256(path: Path) -> str:
    """Return the SHA256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_files() -> list[str]:
    """Extract protected file paths from KEY_DOCUMENTS.md."""
    lines = KEY_DOCS.read_text().splitlines()
    files: list[str] = []
    in_table = False
    for line in lines:
        if line.strip() == "## Protected Files":
            in_table = True
            continue
        if in_table:
            if not line.strip():
                break
            if line.startswith("| ["):
                match = re.search(r"\(([^)]+)\)", line)
                if match:
                    link = match.group(1)
                    path = (KEY_DOCS.parent / link).resolve().relative_to(ROOT)
                    files.append(str(path))
    return files


def main() -> int:
    """Exit non-zero if hashes or summaries are missing or outdated."""
    if not CONFIRM.exists():
        print(
            "onboarding_confirm.yml missing. "
            "Run scripts/confirm_reading.py after reviewing key documents.",
            file=sys.stderr,
        )
        return 1
    try:
        data = yaml.safe_load(CONFIRM.read_text()) or {}
    except yaml.YAMLError as exc:
        print(f"Failed to parse {CONFIRM}: {exc}", file=sys.stderr)
        return 1
    docs: dict[str, object] = data.get("documents", {})
    missing_entries: list[str] = []
    missing_fields: list[str] = []
    mismatched: list[str] = []
    for rel in protected_files():
        entry = docs.get(rel)
        if not isinstance(entry, dict):
            missing_entries.append(rel)
            continue
        sha = entry.get("sha256")
        summary = entry.get("summary")
        if not sha or not summary:
            missing_fields.append(rel)
            continue
        path = ROOT / rel
        if sha256(path) != sha:
            mismatched.append(rel)
    if missing_entries or missing_fields or mismatched:
        for rel in missing_entries:
            print(f"Missing entry for: {rel}", file=sys.stderr)
        for rel in missing_fields:
            print(f"Missing sha256 or summary for: {rel}", file=sys.stderr)
        for rel in mismatched:
            print(f"Hash mismatch for: {rel}", file=sys.stderr)
        print(
            "Update onboarding_confirm.yml with current hashes and summaries.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
