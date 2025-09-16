# NEOABZU Spine

**Version:** v0.1.1
**Last updated:** 2025-10-07

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

## Blueprint Synchronization
Rust crate or pipeline adjustments must update [system_blueprint.md](system_blueprint.md), [blueprint_spine.md](blueprint_spine.md), [The_Absolute_Protocol.md](The_Absolute_Protocol.md#architecture-change-doctrine), and refresh the documentation indexes ([index.md](index.md) and [INDEX.md](INDEX.md)). Run the documentation pre-commit hooks so `doc-indexer` and blueprint verifiers confirm the new crate layout is reflected across the doctrine.

## Version History
- v0.1.1 (2025-10-07): Documented blueprint synchronization requirements for architecture commits.
- v0.1.0 (2025-10-05): Documented identity spine pipeline.
