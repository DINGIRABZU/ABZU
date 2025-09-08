#!/usr/bin/env python3
"""Validate connectors for placeholders and MCP adoption.

The script scans the ``connectors`` directory for two classes of issues:

* placeholder markers such as ``TODO`` or ``TBD``
* raw HTTP usage without mentioning the mandated ``MCP`` protocol

Any detected issue is reported and the process exits with status code 1.
"""
from __future__ import annotations

import re
from pathlib import Path

__version__ = "0.1.0"

# Files allowed to use HTTP without MCP mention
ALLOWED = {
    "connectors/primordials_api.py",
    "connectors/message_formatter.py",
}

PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|FIXME)\b", re.IGNORECASE)
HTTP_PATTERN = re.compile(r"http[s]?://|requests\\.|urllib\\.|httpx\\.")
MCP_PATTERN = re.compile(r"\bMCP\b", re.IGNORECASE)


def scan_file(path: Path) -> tuple[list[int], bool]:
    """Return placeholder line numbers and MCP status for *path*.

    The boolean indicates whether HTTP is used without an MCP reference.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return [], False

    lines = text.splitlines()
    placeholder_lines: list[int] = [
        idx for idx, line in enumerate(lines, 1) if PLACEHOLDER_RE.search(line)
    ]
    missing_mcp = HTTP_PATTERN.search(text) and not MCP_PATTERN.search(text)
    return placeholder_lines, bool(missing_mcp)


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    connector_dir = repo_root / "connectors"

    placeholder_hits: list[tuple[str, int]] = []
    mcp_offenders: list[str] = []

    for py_file in connector_dir.rglob("*.py"):
        rel = py_file.relative_to(repo_root).as_posix()
        placeholders, missing_mcp = scan_file(py_file)
        for line in placeholders:
            placeholder_hits.append((rel, line))
        if missing_mcp and rel not in ALLOWED:
            mcp_offenders.append(rel)

    failed = False
    if placeholder_hits:
        failed = True
        for rel, line in placeholder_hits:
            print(f"Placeholder found: {rel}:{line}")
    if mcp_offenders:
        failed = True
        for rel in mcp_offenders:
            print(f"MCP missing for connector: {rel}")
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
