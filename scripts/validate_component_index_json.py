#!/usr/bin/env python3
"""Validate status and ADR fields in component_index.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "component_index.json"
SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "component_index.json"
ALLOWED_STATUS = {"active", "deprecated", "experimental"}
__version__ = "0.1.0"


def main() -> int:
    """Return 0 if all components declare valid status and ADR fields."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
    except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
        print(f"component_index.json validation failed: {exc}")
        return 1

    errors: list[str] = []
    for comp in data.get("components", []):
        status = comp.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{comp.get('id')}: invalid status '{status}'")
        if "adr" not in comp:
            errors.append(f"{comp.get('id')}: missing adr field")
        else:
            adr = comp.get("adr")
            if isinstance(adr, str):
                adr_path = REPO_ROOT / adr
                if not adr_path.exists():
                    errors.append(f"{comp.get('id')}: adr path '{adr}' not found")
    if errors:
        print("component_index.json validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
