#!/usr/bin/env python3
"""Ensure onboarding_confirm.yml updated when NEOABZU code changes."""
from __future__ import annotations

import subprocess
import sys

NEO_PREFIX = "NEOABZU/"
DOC_PREFIX = "NEOABZU/docs/"
CONFIRM = "onboarding_confirm.yml"
__version__ = "0.1.0"


def _staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [p.strip() for p in result.stdout.splitlines() if p.strip()]


def main() -> int:
    staged = _staged_files()
    neo_changes = [
        f for f in staged if f.startswith(NEO_PREFIX) and not f.startswith(DOC_PREFIX)
    ]
    if neo_changes and CONFIRM not in staged:
        print(
            "onboarding_confirm.yml must be updated when modifying NEOABZU code:",
            file=sys.stderr,
        )
        for path in neo_changes:
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
