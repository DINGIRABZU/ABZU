#!/usr/bin/env python3
"""Ensure onboarding_confirm.yml references required foundational documents."""
from __future__ import annotations

from pathlib import Path
import sys
import yaml

REQUIRED = [
    "docs/blueprint_spine.md",
    "docs/The_Absolute_Protocol.md",
    "NEOABZU/docs/Oroboros_Core.md",
]

ROOT = Path(__file__).resolve().parents[1]
CONFIRM = ROOT / "onboarding_confirm.yml"
__version__ = "0.1.0"


def main() -> int:
    if not CONFIRM.exists():
        print("onboarding_confirm.yml not found", file=sys.stderr)
        return 1
    data = yaml.safe_load(CONFIRM.read_text()) or {}
    documents = data.get("documents", {})
    missing = [doc for doc in REQUIRED if doc not in documents]
    if missing:
        print("onboarding_confirm.yml missing required references:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
