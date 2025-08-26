"""Validate YAML templates and JSON schema files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import validate

SCHEMAS = [
    ("insight_matrix.json", "insight_matrix.schema.json"),
    ("insight_manifest.json", "insight_manifest.schema.json"),
    ("intent_matrix.json", "intent_matrix.schema.json"),
    ("mirror_thresholds.json", "mirror_thresholds.schema.json"),
]


def _validate_templates() -> None:
    for name in [
        "agents/albedo/nazarick_templates.yaml",
        "agents/albedo/rival_templates.yaml",
    ]:
        path = Path(name)
        yaml.safe_load(path.read_text(encoding="utf-8"))


def _validate_schemas() -> None:
    for data_file, schema_file in SCHEMAS:
        data_path = Path(data_file)
        schema_path = Path("schemas") / schema_file
        data = json.loads(data_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validate(data, schema)


def main() -> None:
    _validate_templates()
    _validate_schemas()


if __name__ == "__main__":
    main()
