"""Validate YAML templates and JSON/YAML schema files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate

__version__ = "0.1.0"

SCHEMAS = [
    ("insight_matrix.json", "schemas/insight_matrix.schema.json"),
    ("insight_manifest.json", "schemas/insight_manifest.schema.json"),
    ("intent_matrix.json", "schemas/intent_matrix.schema.json"),
    ("mirror_thresholds.json", "schemas/mirror_thresholds.schema.json"),
    ("razar/boot_config.json", "docs/schemas/boot_config.schema.json"),
    ("razar_env.yaml", "docs/schemas/razar_env.schema.yaml"),
    ("logs/razar_state.json", "docs/schemas/razar_state.schema.json"),
]


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported file type: {path.suffix}")


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
        schema_path = Path(schema_file)
        data = _load(data_path)
        schema = _load(schema_path)
        validate(data, schema)


def main() -> None:
    _validate_templates()
    _validate_schemas()


if __name__ == "__main__":
    main()
