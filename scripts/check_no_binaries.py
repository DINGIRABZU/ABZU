#!/usr/bin/env python3
"""Fail if any staged files are detected as binary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ALLOWED_BINARIES: set[str] = set()
__version__ = "0.1.0"


def staged_binary_files() -> list[str]:
    """Return a list of staged files that appear to be binary."""
    cmd = ["git", "diff", "--cached", "--numstat"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    binaries: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        if added == "-" or removed == "-":
            if not Path(path).exists():
                continue
            if path in ALLOWED_BINARIES:
                continue
            binaries.append(path)
    return binaries


def main() -> int:
    """Return non-zero if binary files are staged for commit."""
    binaries = staged_binary_files()
    if binaries:
        print("Binary files staged for commit:")
        for path in binaries:
            print(f" - {path}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
