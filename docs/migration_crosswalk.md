# Migration Crosswalk

For legacy edge cases, see the [Python legacy audit](python_legacy_audit.md).

| Step | Rust crate | Remaining Python dependencies |
|------|------------|--------------------------------|
| Razor init | `neoabzu_memory` | `razar/boot_orchestrator.py` |
| Crown routing | `neoabzu_crown` | `crown_router.py` |
| Fusion invariants | `neoabzu_fusion` | `NEOABZU/neoabzu/fusion.py` |
| Numeric embeddings | `neoabzu_numeric` | `NEOABZU/neoabzu/numeric.py` |
| Persona context | `neoabzu_persona_layers` | `NEOABZU/neoabzu/persona.py` |
| RAG retrieval | `neoabzu_rag` | `rag/orchestrator.py` |
| Kimicho fallback | `neoabzu_kimicho` | `kimicho.py` |

### Razor init
- [ ] Port complete
- [ ] Required tests: `tests/agents/razar/test_crown_handshake.py`
- [ ] Documentation references: `docs/RAZAR_AGENT.md`

### Crown routing
- [ ] Port complete
- [ ] Required tests: `NEOABZU/crown/tests/route_query.rs`
- [ ] Documentation references: `docs/CROWN_OVERVIEW.md`

### Fusion invariants
- [ ] Port complete
- [ ] Required tests: `NEOABZU/fusion/tests/invariants.rs`
- [ ] Documentation references: `docs/system_blueprint.md`

### Numeric embeddings
- [ ] Port complete
- [ ] Required tests: `tests/test_numeric_cosine_similarity.py`
- [ ] Documentation references: `docs/vector_memory.md`

### Persona context
- [ ] Port complete
- [ ] Required tests: `tests/test_personality_layers.py`
- [ ] Documentation references: `docs/persona_api_guide.md`

### RAG retrieval
- [ ] Port complete
- [ ] Required tests: `NEOABZU/rag/tests/orchestrator.rs`
- [ ] Documentation references: `docs/rag_pipeline.md`

### Kimicho fallback
- [ ] Port complete
- [ ] Required tests: `NEOABZU/kimicho/tests/razor_integration.rs`
- [ ] Documentation references: `docs/system_blueprint.md`

