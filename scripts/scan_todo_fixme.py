#!/usr/bin/env python3
"""Fail if staged code contains TODO or FIXME markers."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

__version__ = "0.1.0"

PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)


def main() -> int:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = [Path(p) for p in diff.stdout.splitlines() if p]
    script_path = Path(__file__).resolve()
    failed = False
    for path in files:
        if path.resolve() == script_path:
            continue
        if path.suffix.lower() == ".md":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for line_no, line in enumerate(content.splitlines(), 1):
            if PLACEHOLDER_RE.search(line):
                print(f"{path}:{line_no}: contains TODO/FIXME marker")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
