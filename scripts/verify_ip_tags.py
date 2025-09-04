"""Validate that all `@ip-sensitive` files appear in the IP registry."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "ip_registry.md"


def find_annotated_files() -> set[str]:
    paths: set[str] = set()
    for path in REPO_ROOT.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            if line.strip().startswith("#") and "@ip-sensitive" in line:
                paths.add(str(path.relative_to(REPO_ROOT)))
                break
    return paths


def registry_entries() -> set[str]:
    entries: set[str] = set()
    if not REGISTRY_PATH.exists():
        return entries
    for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 3:
            entries.add(parts[2])
    return entries


def main() -> int:
    annotated = find_annotated_files()
    registry = registry_entries()
    missing = annotated - registry
    if missing:
        for path in sorted(missing):
            print(f"Annotated file missing from registry: {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
