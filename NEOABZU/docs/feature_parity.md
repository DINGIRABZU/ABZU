# Feature Parity Matrix

Track NEOABZU progress toward ABZU functionality. Update this table as milestones complete to keep contributors aligned.

Refer to the [Rust Doctrine](rust_doctrine.md) for coding conventions.

For the narrative driver and lexicon grounding the engine, see [herojourney_engine.md](herojourney_engine.md) and [SUMERIAN_33WORDS.md](SUMERIAN_33WORDS.md).

| ABZU Module | Status | NEOABZU Plan |
| --- | --- | --- |
| User Interface | Routes user intents through the Persona API【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L39-L40】 | drop |
| Persona API | Normalizes user intents and forwards requests to the Crown Router【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L42-L43】 | migrated via `neoabzu_persona` |
| Crown Router | Coordinates system-level actions and delegates to RAG Orchestrator【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L45-L46】 | rewrite in Rust |
| RAG Orchestrator | Dispatches queries to memory bundle and external sources【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L48-L52】 | Rust orchestrator aggregates memory and connector results |
| Insight Engine | Performs higher-order reasoning and returns insights via Persona API【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L54-L58】 | `neoabzu-insight` counts word frequencies and integrates with Crown Router |
| Memory Bundle | Cortex, Emotional, Mental, Spiritual, and Narrative layers for unified storage【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L48-L49】【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L72-L76】 | reuse |
| System Coordination | Metrics, tracing, and caching align cross-subsystem orchestration | parity achieved |
| Vector Search | Accelerates similarity lookups across memory layers【F:docs/ABZU_SUBSYSTEM_OVERVIEW.md†L72-L76】 | Rust crate `neoabzu_vector` exposed via gRPC |
| Numeric Utilities | Provides fast math primitives | initial Rust crate `neoabzu_numeric` |
| Fusion Engine | Merges symbolic and numeric invariants | initial Rust crate `neoabzu_fusion` |

