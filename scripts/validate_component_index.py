#!/usr/bin/env python3
"""Ensure docs/component_index.md has no empty descriptions."""
from __future__ import annotations

from pathlib import Path

INDEX_PATH = Path("docs/component_index.md")


def main() -> int:
    """Return 0 if all INANNA_AI rows have descriptions."""
    text = INDEX_PATH.read_text(encoding="utf-8")
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.startswith("| `") or line.startswith("| File"):
            continue
        parts = [p.strip() for p in line.strip().split("|")][1:4]
        if len(parts) < 2 or not parts[0].startswith("`INANNA_AI/"):
            continue
        desc = parts[1]
        if desc == "" or desc.lower() == "no description":
            errors.append(f"Line {lineno}: missing description for {parts[0]}")
    if errors:
        print("Component index validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
