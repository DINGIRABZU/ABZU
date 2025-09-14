# Migration Crosswalk

For legacy edge cases, see the [Python legacy audit](python_legacy_audit.md).

| Step | Rust crate | Remaining Python dependencies |
|------|------------|--------------------------------|
| Razor init | `neoabzu_memory` | `razar/boot_orchestrator.py` |
| Crown routing | `neoabzu_crown` | — |
| Fusion invariants | `neoabzu_fusion` | — |
| Numeric embeddings | `neoabzu_numeric` | — |
| Persona context | `neoabzu_persona` | — |
| RAG retrieval | `neoabzu_rag` | `rag/orchestrator.py` |
| Kimicho fallback | `neoabzu_kimicho` | — |

### Razor init
- [x] Port complete
- [x] Required tests: `tests/agents/razar/test_crown_handshake.py`
- [ ] Documentation references: `docs/RAZAR_AGENT.md`

### Crown routing
- [ ] Port complete
- [ ] Required tests: `NEOABZU/crown/tests/route_query.rs`
- [ ] Documentation references: `docs/CROWN_OVERVIEW.md`

### Fusion invariants
- [x] Port complete
- [x] Required tests: `NEOABZU/fusion/tests/invariants.rs`
- [ ] Documentation references: `docs/system_blueprint.md`

### Numeric embeddings
- [x] Port complete
- [x] Required tests: `tests/test_numeric_cosine_similarity.py`
- [ ] Documentation references: `docs/vector_memory.md`

### Persona context
- [x] Port complete
- [x] Required tests: `tests/test_personality_layers.py`
- [ ] Documentation references: `docs/persona_api_guide.md`

### RAG retrieval
- [ ] Port complete
- [ ] Required tests: `NEOABZU/rag/tests/orchestrator.rs`
- [ ] Documentation references: `docs/rag_pipeline.md`

### Kimicho fallback
- [ ] Port complete
- [ ] Required tests: `NEOABZU/kimicho/tests/razor_integration.rs`
- [ ] Documentation references: `docs/system_blueprint.md`

