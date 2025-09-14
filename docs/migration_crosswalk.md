# Migration Crosswalk

For legacy edge cases, see the [Python legacy audit](python_legacy_audit.md).

| Step | Rust crate | Doctrine Reference | Remaining Python dependencies |
|------|------------|--------------------|--------------------------------|
| Razor init | `neoabzu_memory` | [system_blueprint.md#operator-razar-crown-flow](system_blueprint.md#operator-razar-crown-flow) | `razar/boot_orchestrator.py` |
| Crown routing | `neoabzu_crown` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | — |
| Fusion invariants | `neoabzu_fusion` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | — |
| Numeric embeddings | `neoabzu_numeric` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | — |
| Persona context | `neoabzu_persona` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | — |
| RAG retrieval | `neoabzu_rag` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | `rag/orchestrator.py` |
| Kimicho fallback | `neoabzu_kimicho` | [system_blueprint.md#operator-razar-crown-flow](system_blueprint.md#operator-razar-crown-flow) | — |

### Razor init
- [x] Port complete
- [x] Required tests: `tests/agents/razar/test_crown_handshake.py`
- [ ] Documentation references: `docs/RAZAR_AGENT.md`
- [ ] Doctrine references: `docs/system_blueprint.md`

### Crown routing
- [ ] Port complete
- [ ] Required tests: `NEOABZU/crown/tests/route_query.rs`
- [ ] Documentation references: `docs/CROWN_OVERVIEW.md`
- [ ] Doctrine references: `docs/The_Absolute_Protocol.md`

### Fusion invariants
- [x] Port complete
- [x] Required tests: `NEOABZU/fusion/tests/invariants.rs`
- [ ] Documentation references: `docs/system_blueprint.md`
- [ ] Doctrine references: `docs/system_blueprint.md`

### Numeric embeddings
- [x] Port complete
- [x] Required tests: `tests/test_numeric_cosine_similarity.py`
- [ ] Documentation references: `docs/vector_memory.md`
- [ ] Doctrine references: `docs/The_Absolute_Protocol.md`

### Persona context
- [x] Port complete
- [x] Required tests: `tests/test_personality_layers.py`
- [ ] Documentation references: `docs/persona_api_guide.md`
- [ ] Doctrine references: `docs/system_blueprint.md`

### RAG retrieval
- [ ] Port complete
- [ ] Required tests: `NEOABZU/rag/tests/orchestrator.rs`
- [ ] Documentation references: `docs/rag_pipeline.md`
- [ ] Doctrine references: `docs/The_Absolute_Protocol.md`

### Kimicho fallback
- [ ] Port complete
- [x] Required tests: `NEOABZU/kimicho/tests/razor_integration.rs`, `NEOABZU/crown/tests/kimicho_fallback.rs`
- [ ] Documentation references: `docs/system_blueprint.md`
- [ ] Doctrine references: `docs/system_blueprint.md`

