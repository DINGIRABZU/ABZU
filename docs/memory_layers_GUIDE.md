# Memory Layers Guide

## Vision
Coordinates cortex, emotional, mental, spiritual, and narrative stores and
announces their status over the event bus to keep subsystems in sync.

## Architecture
- `scripts/init_memory_layers.py` seeds all stores and publishes `layer_init`
  events.
- `memory/*` modules persist records to file‑backed databases.
- `agents.event_bus` routes cross‑layer messages to subscribed services.

## Deployment
```bash
python scripts/init_memory_layers.py
```
Requires SQLite for emotional, spiritual, and narrative layers. Mental layer
falls back to a skipped state when Neo4j or dependencies are unavailable.

## Example Runs
```bash
pytest tests/test_memory_bus.py::test_init_memory_layers_bootstrap_and_persist
```

## Cross-Links
- [Narrative Engine Guide](narrative_engine_GUIDE.md)
- [Nazarick Guide](Nazarick_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-09-23 | Documented memory layer event flow and persistence check. |
