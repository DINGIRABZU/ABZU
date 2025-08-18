# Architecture Overview

This guide explains in plain language how a request travels through Spiral OS. For a chakra‑oriented map of the codebase, see [spiritual_architecture.md](spiritual_architecture.md).

### Request Flow

```mermaid
flowchart LR
    U[User request] --> O[Orchestrator]
    O --> R[LLM router]
    R --> M[Model registry]
    M --> L[Selected model]
    L --> A[Audio pipeline]
    A --> S[Avatar or text response]
```

### LLM Router
The LLM router acts as a traffic controller for prompts. When a message arrives, `crown_router.py` checks recent emotion stored in `vector_memory` and chooses a language model and voice that fit the conversation. It returns both the model choice and hints for speech style so replies stay in tune with the current mood.

### Model Registry
`servant_model_manager.py` is a catalogue of helper models. Each servant registers a name and how to run it—either as a Python function or an external process. The orchestrator asks this registry to invoke a model by name, making it straightforward to plug in new specialised tools.

### Audio Pipeline
The audio pipeline has two stops. `audio_ingestion.py` brings in clips and analyses features such as tempo, key and CLAP embeddings. `audio_engine.py` then plays the sound, adds effects or synthesises missing notes. Together they handle capture, analysis and playback.

