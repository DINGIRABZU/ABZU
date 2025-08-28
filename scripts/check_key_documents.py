#!/usr/bin/env python3
"""Verify that key documents exist."""
from __future__ import annotations
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "key_documents.yml"


def main() -> int:
    """Exit with non-zero status if any key document is missing."""
    data = yaml.safe_load(CONFIG.read_text())
    files = data.get("files", [])
    missing = [f for f in files if not (ROOT / f).exists()]
    if missing:
        for f in missing:
            print(f"Missing required file: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
