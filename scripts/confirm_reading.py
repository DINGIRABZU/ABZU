#!/usr/bin/env python3
"""Ensure the onboarding checklist has been completed."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / ".reading_complete"


def main() -> int:
    """Exit non-zero if the reading completion marker is missing."""
    if not MARKER.exists():
        message = (
            "Onboarding checklist not confirmed. "
            "Create '.reading_complete' in the repo root "
            "after completing the checklist."
        )
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
