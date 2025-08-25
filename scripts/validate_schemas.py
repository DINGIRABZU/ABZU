"""Validate JSON files against their JSON Schemas."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def main() -> None:
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        data_path = ROOT / schema_path.name.replace(".schema", "")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        data = json.loads(data_path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
        print(f"Validated {data_path.name}")


if __name__ == "__main__":
    main()
