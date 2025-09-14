# Architecture Overview

For broader project context read [project_overview.md](project_overview.md)
and [README_CODE_FUNCTION.md](../README_CODE_FUNCTION.md). A consolidated
reference lives in [CRYSTAL_CODEX.md](../CRYSTAL_CODEX.md).

This guide breaks down Spiral OS into its primary components. Each section
includes a small diagram, links to implementation and tests, and a brief note
on how the design has evolved.

Architecture decisions are recorded as [ADRs](adr/). Key choices include
[using FAISS for vector search](adr/0001-use-faiss-for-vector-search.md) and
[preferring asyncio over threads](adr/0002-prefer-asyncio-over-threads.md).

## Router

```mermaid
flowchart LR
    R[Router] --> EA[Emotion Analyzer]
    R --> MS[Model Selector]
    R --> ML[Memory Logger]
```

- [`neoabzu_crown`](../NEOABZU/crown/src/lib.rs)
- Tests: [tests/crown/test_crown_router_memory.py](../tests/crown/test_crown_router_memory.py)

**Design Evolution:** Score 2; depends on `rag`.

## Emotion Analyzer

```mermaid
flowchart LR
    Text --> EA[Emotion Analyzer] --> Mood
```

- [src/core/emotion_analyzer.py](../src/core/emotion_analyzer.py)
- Tests: [tests/test_core_services.py](../tests/test_core_services.py)

**Design Evolution:** Score 1; depends on `INANNA_AI`.

## Model Selector

```mermaid
flowchart LR
    Context --> MS[Model Selector] --> Model
```

- [src/core/model_selector.py](../src/core/model_selector.py)
- Tests: [tests/test_core_services.py](../tests/test_core_services.py)

**Design Evolution:** Score 1; depends on `INANNA_AI`.

## Memory Logger

```mermaid
flowchart LR
    Event --> ML[Memory Logger] --> Stores
```

- [src/core/memory_logger.py](../src/core/memory_logger.py)
- Tests: [tests/test_core_services.py](../tests/test_core_services.py)

**Design Evolution:** Score 1; no external dependencies.

## Cortex Memory

```mermaid
flowchart LR
    ML[Memory Logger] --> Cortex
    Cortex --> Query
```

- [memory/cortex.py](../memory/cortex.py)
- Tests: [tests/test_cortex_memory.py](../tests/test_cortex_memory.py)

**Design Evolution:** Score 1; no external dependencies.

## Spiral Cortex Memory

```mermaid
flowchart LR
    ML[Memory Logger] --> SC[Spiral Cortex]
    SC --> Insight
```

- [memory/spiral_cortex.py](../memory/spiral_cortex.py)
- Tests: [tests/test_spiral_cortex_memory.py](../tests/test_spiral_cortex_memory.py)

**Design Evolution:** Score 1; no external dependencies.

## Emotional Memory

```mermaid
flowchart LR
    EA[Emotion Analyzer] --> EM[Emotional Memory] --> History
```

- [memory/emotional.py](../memory/emotional.py)
- Tests: [tests/test_memory_emotional.py](../tests/test_memory_emotional.py)

**Design Evolution:** Score 2; depends on `dlib`, `transformers`.

## Mental Memory

```mermaid
flowchart LR
    Reasoning --> MM[Mental Memory] --> State
```

- [memory/mental.py](../memory/mental.py)
- Tests: [tests/test_seven_dimensional_music.py](../tests/test_seven_dimensional_music.py)

**Design Evolution:** Score 1; depends on `core`, `crown_config`.

## Spiritual Memory

```mermaid
flowchart LR
    Symbol --> SM[Spiritual Memory] --> Meaning
```

- [memory/spiritual.py](../memory/spiritual.py)
- Tests: [tests/test_memory_spiritual.py](../tests/test_memory_spiritual.py)

**Design Evolution:** Score 2; no external dependencies.

## Sacred Memory

```mermaid
flowchart LR
    Image --> SaM[Sacred Memory] --> Archive
```

- [memory/sacred.py](../memory/sacred.py)
- Tests: [tests/test_vast_pipeline.py](../tests/test_vast_pipeline.py)

**Design Evolution:** Score 1; depends on `PIL`, `torch`.

## Cortex Sigil Labs

```mermaid
flowchart LR
    Symbol --> CS[Cortex Sigil] --> Trigger
```

- [labs/cortex_sigil.py](../labs/cortex_sigil.py)
- Tests: [tests/test_cortex_sigil_logic.py](../tests/test_cortex_sigil_logic.py)

**Design Evolution:** Score 1; no external dependencies.
