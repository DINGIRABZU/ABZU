# Migration Crosswalk

This crosswalk outlines how memory layers connect to Crown during startup.

- The `neoabzu_memory` bundle initializes emotional, mental, spiritual, and narrative layers and
  broadcasts a `layer_init` event over the bus.
- `neoabzu_crown` imports this bundle at module load and exposes `query_memory`,
  routing memory queries through Crown while preserving layer aggregation.
- `fusion` merges invariants from symbolic and numeric streams before broadcast.
- `numeric` refines memory embeddings via principal component analysis.
- `neoabzu_persona_layers` injects persona context that Crown uses during routing.
- `neoabzu_rag` queries the bundle to retrieve supporting documents for prompts.
- Integration tests validate the broadcast and the query path.
- The Rust module also handles Crown routing formerly in `crown_router.py`, adding validation, orchestrator delegation, and telemetry hooks.
