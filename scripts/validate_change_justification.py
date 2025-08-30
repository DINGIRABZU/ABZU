#!/usr/bin/env python3
"""Verify pull requests include a Change Justification statement."""
from __future__ import annotations

import json
import os
import re
import sys

__version__ = "0.1.0"

PATTERN = re.compile(r"I did .+ on .+ to obtain .+, expecting behavior .+\.")


def main() -> int:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        print("GITHUB_EVENT_PATH not set", file=sys.stderr)
        return 1
    with open(event_path, encoding="utf-8") as f:
        body = json.load(f).get("pull_request", {}).get("body", "")

    if "Change Justification" not in body:
        print("Missing Change Justification section", file=sys.stderr)
        return 1
    if "I did X on Y to obtain Z, expecting behavior B." in body:
        print("Change Justification uses placeholder text", file=sys.stderr)
        return 1
    if not PATTERN.search(body):
        print("Change Justification not in required format", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
