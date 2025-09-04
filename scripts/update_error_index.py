#!/usr/bin/env python3
"""Parse logs and append new errors to docs/error_registry.md."""
from __future__ import annotations

import re
from pathlib import Path

LOG_DIR = Path("logs")
DOC_PATH = Path("docs/error_registry.md")
ERROR_SECTION = "## Logged Errors"
ERROR_PATTERN = re.compile(r"error[: ]+(.*)", re.IGNORECASE)


def collect_errors() -> set[str]:
    """Return a set of error lines parsed from text log files."""
    errors: set[str] = set()
    for path in LOG_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".log", ".txt"}:
            try:
                text = path.read_text(errors="ignore")
            except Exception:
                continue
            for line in text.splitlines():
                if ERROR_PATTERN.search(line):
                    errors.add(line.strip())
    return errors


def parse_doc() -> tuple[list[str], set[str], int]:
    """Return document lines, existing errors, and insertion index."""
    if DOC_PATH.exists():
        lines = DOC_PATH.read_text().splitlines()
    else:
        lines = ["# Error Registry", "", ERROR_SECTION, ""]
    try:
        start = lines.index(ERROR_SECTION) + 1
    except ValueError:
        lines.extend(["", ERROR_SECTION, ""])
        start = lines.index(ERROR_SECTION) + 1
    existing = {line[2:].strip() for line in lines[start:] if line.startswith("- ")}
    insert_pos = start + len([line for line in lines[start:] if line.startswith("- ")])
    return lines, existing, insert_pos


def main() -> None:
    errors = collect_errors()
    if not errors:
        return
    lines, existing, insert_pos = parse_doc()
    new_errors = sorted(e for e in errors if e not in existing)
    if not new_errors:
        return
    for e in new_errors:
        lines.insert(insert_pos, f"- {e}")
        insert_pos += 1
    DOC_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
