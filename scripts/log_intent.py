#!/usr/bin/env python3
"""Append commit intent entries to the change ledger."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Optional


__version__ = "0.1.0"


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Log commit intent and observed behavior"
    )
    parser.add_argument("intent", help="Reason or purpose behind the change")
    parser.add_argument("observed_behavior", help="Behavior observed after the change")
    parser.add_argument(
        "--commit",
        default=None,
        help="Commit hash to record (defaults to HEAD)",
    )
    args = parser.parse_args(argv)

    commit = args.commit
    if commit is None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    entry = {
        "commit_hash": commit,
        "intent": args.intent,
        "observed_behavior": args.observed_behavior,
    }

    log_path = Path("logs/change_intent.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"Logged intent for {commit}.")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
