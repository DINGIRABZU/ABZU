#!/usr/bin/env python3
"""Parse log files and append unique error lines to the error registry."""
from __future__ import annotations

import re
from pathlib import Path

LOG_DIR = Path("logs")
REGISTRY_PATH = Path("docs/error_registry.md")


def extract_errors() -> set[str]:
    """Return a set of unique error messages from files under ``logs/``."""
    errors: set[str] = set()
    if not LOG_DIR.exists():
        return errors
    for path in LOG_DIR.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for line in text.splitlines():
            if "error" in line.lower():
                match = re.search(r'"error"\s*:\s*"([^"]+)"', line, re.IGNORECASE)
                if match:
                    errors.add(match.group(1).strip())
                else:
                    errors.add(line.strip())
    return errors


def load_existing() -> set[str]:
    """Load error strings already present in the registry."""
    existing: set[str] = set()
    if not REGISTRY_PATH.exists():
        return existing
    for line in REGISTRY_PATH.read_text().splitlines():
        if line.startswith("- "):
            existing.add(line[2:].strip())
    return existing


def main() -> None:
    errors = extract_errors()
    if not errors:
        return
    existing = load_existing()
    new_errors = sorted(e for e in errors if e not in existing)
    if not new_errors:
        return

    lines = REGISTRY_PATH.read_text().splitlines() if REGISTRY_PATH.exists() else []
    if "## Logged Errors" not in lines:
        lines.extend(["", "## Logged Errors", ""])
    lines.extend([f"- {err}" for err in new_errors])
    lines.append("")
    REGISTRY_PATH.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
