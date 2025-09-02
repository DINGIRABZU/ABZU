# INANNA Guide

## Vision
INANNA provides the core GLM interface and memory access for Crown.

## Architecture
- Loads GLM-4.1V model or delegates to remote endpoint.
- Stores persistent state under `data/vector_memory`.
- Routes prompts to optional servant models.

## Deployment
```bash
export GLM_API_URL=https://glm.example.com
mkdir -p data/vector_memory/{vector_memory,chroma}
python -m INANNA_AI.corpus_memory --reindex
```

## Configuration Schemas
- `crown_config/INANNA_CORE.yaml` — API URLs, model paths, memory directory, servant model endpoints.

## Example Runs
```bash
python -m INANNA_AI.main --duration 3 --personality albedo
```

## Cross-Links
- [Crown Guide](Crown_GUIDE.md)
- [Memory Layers Guide](memory_layers_GUIDE.md)
- [Vector Memory](vector_memory.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-08-30 | Initial configuration guide. |
