"""Tests for schema validation."""

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent


def test_insight_json_files_validate():
    files = [
        ("insight_matrix.json", "insight_matrix.schema.json"),
        ("intent_matrix.json", "intent_matrix.schema.json"),
        ("mirror_thresholds.json", "mirror_thresholds.schema.json"),
        ("insight_manifest.json", "insight_manifest.schema.json"),
    ]
    for json_name, schema_name in files:
        data = json.loads((ROOT / json_name).read_text())
        schema = json.loads((ROOT / "schemas" / schema_name).read_text())
        jsonschema.validate(data, schema)


def test_manifest_checksums_match_files():
    manifest = json.loads((ROOT / "insight_manifest.json").read_text())
    for name in ["insight_matrix", "mirror_thresholds", "intent_matrix"]:
        path = ROOT / f"{name}.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert manifest["checksums"][name] == digest
