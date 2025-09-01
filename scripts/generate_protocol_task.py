#!/usr/bin/env python3
"""Create protocol refinement task after enough registry entries."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request

__version__ = "0.1.0"

REGISTRY_PATH = Path("logs/task_registry.jsonl")
STUB_PATH = Path("logs/refine_protocol_task_stub.md")
ISSUE_TITLE = "Refine The Absolute Protocol"


def load_registry() -> List[Dict[str, Any]]:
    """Return all entries from the task registry."""
    if not REGISTRY_PATH.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def count_since_last_refinement(entries: List[Dict[str, Any]]) -> int:
    """Return number of entries since the last refinement task."""
    last_index = -1
    for i in range(len(entries) - 1, -1, -1):
        if entries[i].get("description") == ISSUE_TITLE:
            last_index = i
            break
    return len(entries) - (last_index + 1)


def create_issue(count: int) -> Optional[str]:
    """Attempt to open a GitHub issue; return its URL on success."""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not token or not repo:
        return None
    payload = json.dumps(
        {
            "title": ISSUE_TITLE,
            "body": f"Automatically generated after {count} new tasks.",
        }
    ).encode("utf-8")
    url = f"https://api.github.com/repos/{repo}/issues"
    req = request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "generate-protocol-task",
        },
    )
    try:
        with request.urlopen(req) as resp:
            data = json.load(resp)
        return data.get("html_url")
    except Exception:
        return None


def create_stub(count: int) -> str:
    """Write a local stub file and return its path."""
    STUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    STUB_PATH.write_text(
        f"# {ISSUE_TITLE}\n\nAutomatically generated after {count} new tasks.\n",
        encoding="utf-8",
    )
    return STUB_PATH.as_posix()


def log_action() -> None:
    """Append a refinement entry to the registry."""
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "task_id": f"refine-protocol-{timestamp}",
        "description": ISSUE_TITLE,
        "component_id": "protocol",
        "contributor": "automation",
        "pr_number": 0,
        "completed_at": timestamp,
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main() -> None:
    """Trigger protocol refinement task when threshold met."""
    entries = load_registry()
    count = count_since_last_refinement(entries)
    if count < 6:
        print("No refinement needed.")
        return
    url = create_issue(count)
    if url:
        print(f"Issue created at {url}")
    else:
        stub = create_stub(count)
        print(f"Stub created at {stub}")
    log_action()


if __name__ == "__main__":
    main()
