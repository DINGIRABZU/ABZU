# Feature Parity Matrix

Tracks Rust reimplementations of key Python subsystems.

| Component | Rust crate | Notes |
| --- | --- | --- |
| Memory Bundle | `neoabzu_memory` | Initializes layered memory and routes multi‑layer queries. |
| Fusion Engine | `neoabzu_fusion` | Selects invariants with highest inevitability gradient. |
| Numeric Kernels | `neoabzu_numeric` | PCA and cosine similarity utilities via PyO3. |
| Persona API | `neoabzu_persona` | Tracks persona state and loads profile data. |
| Crown Router | `neoabzu_crown` | Direct PyO3 interface with validation, `MoGEOrchestrator` calls, and telemetry parity. |
| RAG Orchestrator | `neoabzu_rag` | Merges memory records and external connector results via `MemoryBundle`. |
