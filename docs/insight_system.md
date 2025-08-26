# Insight System

The insight system aggregates interaction logs into structured matrices used by
reflection and adaptive learning components.

## Manifest

`insight_manifest.json` tracks the semantic versions and SHA-256 checksums for
`insight_matrix.json`, `mirror_thresholds.json`, and `intent_matrix.json`.
It records every update with a timestamp and version history so CI jobs can
verify that the matrices match the expected state.

## Validation

Validate JSON structures against their schemas before committing changes:

```bash
python -m jsonschema ./schemas/insight_matrix.schema.json ./insight_matrix.json
python -m jsonschema ./schemas/mirror_thresholds.schema.json ./mirror_thresholds.json
python -m jsonschema ./schemas/intent_matrix.schema.json ./intent_matrix.json
python -m jsonschema ./schemas/insight_manifest.schema.json ./insight_manifest.json
```

The test suite runs these checks automatically via
`tests/test_insight_compiler.py`.
