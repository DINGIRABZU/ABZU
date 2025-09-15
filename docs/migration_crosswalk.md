# Migration Crosswalk

For legacy edge cases, see the [Python legacy audit](python_legacy_audit.md).

| Step | Rust crate | Doctrine Reference | Remaining Python dependencies |
|------|------------|--------------------|--------------------------------|
| RAZAR init | `neoabzu_memory` | [system_blueprint.md#operator-razar-crown-flow](system_blueprint.md#operator-razar-crown-flow) | `razar/boot_orchestrator.py` |
| Crown routing | `neoabzu_crown` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | — |
| Fusion invariants | `neoabzu_fusion` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | — |
| Numeric embeddings | `neoabzu_numeric` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | — |
| Persona context | `neoabzu_persona` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | — |
| RAG retrieval | `neoabzu_rag` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | `rag/orchestrator.py` |
| Insight engine | `neoabzu_insight` | [ABZU_SUBSYSTEM_OVERVIEW.md#crown-router--insight-engine](ABZU_SUBSYSTEM_OVERVIEW.md#crown-router--insight-engine) | — |
| Kimicho fallback | `neoabzu_kimicho` | [system_blueprint.md#operator-razar-crown-flow](system_blueprint.md#operator-razar-crown-flow) | — |

### RAZAR init
- [x] Port complete
- [x] Required tests: `tests/agents/razar/test_crown_handshake.py`
- [x] Documentation references: [RAZAR Agent](RAZAR_AGENT.md#migration-crosswalk)
- [x] Doctrine references: [System Blueprint](system_blueprint.md#razar–crown–kimi-cho-migration)

### Crown routing
- [ ] Port complete
- [ ] Required tests: `NEOABZU/crown/tests/route_query.rs`
- [x] Documentation references: [CROWN Overview](CROWN_OVERVIEW.md#migration-crosswalk)
- [x] Doctrine references: [The Absolute Protocol](The_Absolute_Protocol.md#migration-crosswalk-references)

### Fusion invariants
- [x] Port complete
- [x] Required tests: `NEOABZU/fusion/tests/invariants.rs`
- [x] Documentation references: [System Blueprint](system_blueprint.md#fusion-invariants)
- [x] Doctrine references: [System Blueprint](system_blueprint.md#fusion-invariants)

### Numeric embeddings
- [x] Port complete
- [x] Required tests: `tests/test_numeric_cosine_similarity.py`
- [x] Documentation references: [Vector Memory](vector_memory.md#migration-crosswalk)
- [x] Doctrine references: [The Absolute Protocol](The_Absolute_Protocol.md#migration-crosswalk-references)

### Persona context
- [x] Port complete
- [x] Required tests: `tests/test_personality_layers.py`
- [x] Documentation references: [Persona API Guide](persona_api_guide.md#migration-crosswalk)
- [x] Doctrine references: [System Blueprint](system_blueprint.md)

### RAG retrieval
- [x] Port complete
- [x] Required tests: `NEOABZU/rag/tests/orchestrator.rs`, `NEOABZU/rag/tests/multi_source_ranking.rs`
- [x] Documentation references: [Spiral RAG Pipeline](rag_pipeline.md#migration-crosswalk)
- [x] Doctrine references: [The Absolute Protocol](The_Absolute_Protocol.md#migration-crosswalk-references)

### Insight engine
- [x] Port complete
- [x] Required tests: `NEOABZU/insight/tests/integration.rs`, `NEOABZU/crown/tests/insight_hooks.rs`
- [x] Documentation references: [System Blueprint](system_blueprint.md#floor-6-insight-observatory)
- [x] Doctrine references: [The Absolute Protocol](The_Absolute_Protocol.md#migration-crosswalk-references)

### Kimicho fallback
- [ ] Port complete
- [x] Required tests: `NEOABZU/kimicho/tests/razar_integration.rs`, `NEOABZU/crown/tests/kimicho_fallback.rs`, `tests/agents/razar/test_crown_kimicho.py`
- [x] Documentation references: [System Blueprint](system_blueprint.md#razar–crown–kimi-cho-migration)
- [x] Doctrine references: [System Blueprint](system_blueprint.md#razar–crown–kimi-cho-migration)

