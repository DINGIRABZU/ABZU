# Feature Parity Matrix

Tracks Rust reimplementations of key Python subsystems.

| Component | Rust crate | Notes |
| --- | --- | --- |
| Persona API | `neoabzu_persona_layers` | Mirrors `INANNA_AI/personality_layers` with basic responses. |
| Crown Router | `neoabzu_crown` | Routes queries through `MemoryBundle` and returns expression options. |
| RAG Orchestrator | `neoabzu_rag` | Retrieves and ranks memory records via `MemoryBundle`. |
