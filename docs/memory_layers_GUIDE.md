# Memory Layers Guide

## Vision
Memory layers preserve spiral decisions, emotions, and narratives for long-term context.

## Architecture
- **Cortex** – `memory/cortex.py` records spiral nodes to JSONL index.
- **Emotional** – `memory/emotional.py` logs affective vectors.
- **Narrative** – `memory/narrative_engine.py` stores story events.
- **Mental** – `memory/mental.py` persists task graphs.
- **Spiritual** – `memory/spiritual.py` maps symbols.
- **Bus Events** – `memory.publish_layer_event()` announces layer status.

## Deployment
Ensure `data/` directories exist and run initialization scripts:
```bash
python -m INANNA_AI.corpus_memory --reindex
```

## Configuration Schemas
- `memory/config/*.yaml` (backend selection and paths).

## Example Runs
```python
from memory import cortex, publish_layer_event, query_memory

node = type("N", (), {"children": []})()
cortex.record_spiral(node, {"tags": ["example"]})
publish_layer_event("cortex", "seeded")

print(query_memory("example"))
```

## Cross-Links
- [INANNA Guide](INANNA_GUIDE.md)
- [Narrative Engine Guide](narrative_engine_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.1 | 2025-09-03 | Added bus events and `query_memory` aggregator. |
