# Architecture Overview

This guide explains in plain language how a request travels through Spiral OS. For a chakra‑oriented map of the codebase, see [spiritual_architecture.md](spiritual_architecture.md).

## Canonical Diagram

```mermaid
graph TD
    subgraph Core
        Router
        "Emotion Analyzer"
        "Model Selector"
        "Memory Logger"
    end
    subgraph Memory
        "memory.cortex"
        "memory.spiral_cortex"
        "memory.emotional"
    end
    subgraph Labs
        "labs.cortex_sigil"
    end
    Router --> "Emotion Analyzer" --> "Model Selector" --> "Memory Logger"
    "Memory Logger" --> "memory.cortex"
    "Memory Logger" --> "memory.spiral_cortex"
    Router --> "labs.cortex_sigil"
```

### Service Contracts

- `core.emotion_analyzer.EmotionAnalyzer` – classify mood of incoming text.
- `core.model_selector.ModelSelector` – choose the appropriate language model.
- `memory.cortex` – `record_spiral` / `query_spirals` for spiral decisions.
- `memory.spiral_cortex` – `log_insight` / `load_insights` for retrieval traces.
- `labs.cortex_sigil` – `interpret_sigils` to extract symbolic triggers.

### Inter-module Dependencies

- `recursive_emotion_router` persists results via `memory.cortex` and augments decisions with `labs.cortex_sigil`.
- `crown_prompt_orchestrator` maps experiences with `memory.mental`, `memory.spiritual`, and `memory.sacred`.
- `rag.retriever` records search context to `memory.spiral_cortex`.

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

