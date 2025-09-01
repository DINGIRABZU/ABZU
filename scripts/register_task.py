#!/usr/bin/env python3
"""Append completed task details to the task registry."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

__version__ = "0.1.0"

REGISTRY_PATH = Path("logs/task_registry.jsonl")


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Record a completed task in the registry.",
    )
    parser.add_argument(
        "--task-id", required=True, help="Unique identifier for the task."
    )
    parser.add_argument("--description", required=True, help="Short task description.")
    parser.add_argument("--component-id", required=True, help="Related component ID.")
    parser.add_argument(
        "--contributor", required=True, help="Contributor name or handle."
    )
    parser.add_argument("--pr", type=int, required=True, help="Pull request number.")
    return parser.parse_args()


def main() -> None:
    """Append a task entry to the registry."""
    args = parse_args()
    entry = {
        "task_id": args.task_id,
        "description": args.description,
        "component_id": args.component_id,
        "contributor": args.contributor,
        "pr_number": args.pr,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    main()
