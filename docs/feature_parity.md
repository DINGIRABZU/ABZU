# Feature Parity Matrix

Tracks Rust reimplementations of key Python subsystems.

| Component | Rust crate | Doctrine Reference | Notes |
| --- | --- | --- | --- |
| Memory Bundle | `neoabzu_memory` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | Initializes layered memory and routes multi‑layer queries. |
| Fusion Engine | `neoabzu_fusion` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | Selects invariants with highest inevitability gradient. |
| Numeric Kernels | `neoabzu_numeric` | [system_blueprint.md#triadic-stack](system_blueprint.md#triadic-stack) | PCA and cosine similarity utilities via PyO3. |
| Persona API | `neoabzu_persona` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | Tracks persona state and loads profile data. |
| Crown Router | `neoabzu_crown` | [system_blueprint.md#operator-razar-crown-flow](system_blueprint.md#operator-razar-crown-flow) | Direct PyO3 interface with validation, `MoGEOrchestrator` calls, and telemetry parity. |
| RAG Orchestrator | `neoabzu_rag` | [The_Absolute_Protocol.md#doctrine-reference-requirements](The_Absolute_Protocol.md#doctrine-reference-requirements) | Aggregates memory and connector retrievals with pluggable ranking strategies via `MemoryBundle`. |
| Insight Engine | `neoabzu_insight` | [ABZU_SUBSYSTEM_OVERVIEW.md#crown-router--insight-engine](ABZU_SUBSYSTEM_OVERVIEW.md#crown-router--insight-engine) | Computes word and bigram embeddings with per‑word semantic scores; Crown Router consumes them via PyO3 hooks. |
