# NEOABZU Spine

**Version:** v0.1.0  
**Last updated:** 2025-10-05

## RAG + Insight Pipeline
After Crown's LLM boots, `neoabzu_crown.load_identity` runs a retrieval and
insight pass over mission, vision, and persona documents. Chunks are embedded
into vector memory, summarized by the GLM, and the resulting identity is
persisted at `data/identity.json` so subsequent invocations reuse the cached
context.

### Doctrine References
- [system_blueprint.md#razar–crown–kimi-cho-migration](system_blueprint.md#razar–crown–kimi-cho-migration)
- [persona_api_guide.md](persona_api_guide.md)
- [project_mission_vision.md](project_mission_vision.md)

## Version History
- v0.1.0 (2025-10-05): Documented identity spine pipeline.
