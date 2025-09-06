"""Validate and update component index entries with required fields."""

from __future__ import annotations

__version__ = "0.1.0"

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict

REQUIRED_FIELDS = [
    "status",
    "usage",
    "version",
    "function",
    "date_created",
    "last_modified",
]

DEFAULTS = {
    "status": "unknown",
    "usage": "unknown",
    "version": "0.0.0",
    "function": "unknown",
}


def update_component(component: Dict[str, Any], today: str) -> bool:
    """Ensure a component has all required fields.

    Returns True if the component was modified.
    """
    updated = False
    for field in REQUIRED_FIELDS:
        if field not in component:
            if field in {"date_created", "last_modified"}:
                component[field] = today
            else:
                component[field] = DEFAULTS.get(field, "unknown")
            updated = True
    if updated:
        component["last_modified"] = today
    return updated


def process_index(path: Path, write: bool) -> int:
    data = json.loads(path.read_text())
    today = dt.date.today().isoformat()
    changes = 0
    for component in data.get("components", []):
        if update_component(component, today):
            changes += 1
    if write and changes:
        path.write_text(json.dumps(data, indent=2) + "\n")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to component_index.json")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write updates back to the file if changes are needed",
    )
    args = parser.parse_args()
    changes = process_index(args.path, args.write)
    if changes:
        print(f"Updated {changes} components.")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    main()
