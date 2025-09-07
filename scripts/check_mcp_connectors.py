#!/usr/bin/env python3
"""Verify connectors use MCP instead of raw HTTP endpoints."""
from __future__ import annotations

import pathlib
import re

# Files allowed to use raw HTTP despite MCP mandate
ALLOWED = {
    "connectors/primordials_api.py",
    "connectors/message_formatter.py",
}

# regex patterns for HTTP usage and MCP references
HTTP_PATTERN = re.compile(r"http[s]?://|requests\\.|urllib\\.|httpx\\.")
MCP_PATTERN = re.compile(r"\bMCP\b", re.IGNORECASE)


def scan_file(path: pathlib.Path) -> bool:
    """Return True if file uses HTTP without MCP mention."""
    text = path.read_text(encoding="utf-8")
    if HTTP_PATTERN.search(text) and not MCP_PATTERN.search(text):
        return True
    return False


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    connector_dir = repo_root / "connectors"

    offenders: list[str] = []
    for py_file in connector_dir.rglob("*.py"):
        rel = py_file.relative_to(repo_root).as_posix()
        if rel in ALLOWED:
            continue
        if scan_file(py_file):
            offenders.append(rel)

    if offenders:
        for rel in offenders:
            print(f"MCP missing for connector: {rel}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
