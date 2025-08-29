#!/usr/bin/env python3
"""Ensure touched connectors have registry entries.

This hook checks the Git staged changes for files in the ``connectors``
package. For each touched connector module, an entry must exist in
``docs/connectors/CONNECTOR_INDEX.md`` matching the connector's id.

A connector id is derived from filenames following the pattern
``<id>_connector.py``. For example, ``connectors/webrtc_connector.py`` has
an id of ``webrtc``. If any touched connector lacks a corresponding entry
in the index, the hook fails with a descriptive message.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import re

__version__ = "0.1.0"

INDEX_PATH = Path("docs/connectors/CONNECTOR_INDEX.md")
CONNECTOR_DIR = Path("connectors")


def get_staged_files() -> list[str]:
    """Return a list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def extract_connector_ids(files: list[str]) -> list[str]:
    """Extract connector ids from staged files."""
    ids: list[str] = []
    pattern = re.compile(r"^connectors/(.+)_connector\.py$")
    for file in files:
        match = pattern.match(file)
        if match:
            ids.append(match.group(1))
    return ids


def load_index() -> str:
    """Read the connector index file."""
    try:
        return INDEX_PATH.read_text()
    except FileNotFoundError:
        print(f"Missing {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)


def ensure_entries(ids: list[str], index_text: str) -> int:
    """Return non-zero if any connector ids are missing from the index."""
    missing = [cid for cid in ids if cid not in index_text]
    if missing:
        print(
            "Missing connector entries in CONNECTOR_INDEX.md: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    """Entrypoint for pre-commit hook."""
    files = get_staged_files()
    ids = extract_connector_ids(files)
    if not ids:
        return 0
    index_text = load_index()
    return ensure_entries(ids, index_text)


if __name__ == "__main__":
    raise SystemExit(main())
