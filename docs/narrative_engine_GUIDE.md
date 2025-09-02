# Narrative Engine Guide

## Vision
Transforms biosignal streams into structured StoryEvents and stores them for later storytelling.

## Architecture
- `scripts/ingest_biosignals.py` normalizes sensor data.
- `bana/event_structurizer.py` validates events.
- `memory/narrative_engine.py` persists events to SQLite and Chroma.

## Deployment
```bash
python scripts/ingest_biosignals.py data/biosignals/sample_biosignals_anonymized.csv
```
Requires SQLite and optional ChromaDB for vector search.

## Configuration Schemas
- Event JSON schema in `bana/event_structurizer.py`.

## Example Runs
```bash
pytest tests/narrative_engine/test_biosignal_pipeline.py
```

## Cross-Links
- [Nazarick Guide](Nazarick_GUIDE.md)
- [Memory Layers Guide](memory_layers_GUIDE.md)
- [Operator Interface Guide](operator_interface_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.6.0 | 2025-09-16 | Clarified architecture and dataset schema. |
