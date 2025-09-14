# Feature Parity Matrix

Tracks Rust reimplementations of key Python subsystems.

| Component | Rust crate | Notes |
| --- | --- | --- |
| Persona API | `neoabzu_persona_layers` | Mirrors `INANNA_AI/personality_layers` with basic responses. |
| Crown Router | `neoabzu_crown` | Replaces `crown_router.py` with validation, `MoGEOrchestrator` calls, and telemetry parity. |
| RAG Orchestrator | `neoabzu_rag` | Merges memory records and external connector results via `MemoryBundle`. |
