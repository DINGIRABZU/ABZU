# Architecture

This guide maps the core packages that shape the ABZU system and how they
cooperate.

## SPIRAL_OS

`SPIRAL_OS` houses the Quantum Narrative Language (QNL) engine and symbolic
parser. The QNL engine converts hexadecimal or text input into tonal
representations and waveforms. The symbolic parser inspects parsed QNL data to
derive intents that influence downstream routing.

## Audio Modules

The `audio` package provides ingestion, digital signal processing and playback.
`audio_ingestion.py` analyses imported clips, `dsp_engine.py` applies effects
such as pitch shifting or time stretching, and `engine.py` plays or loops
samples for rituals and responses.

## RAG Components

Retrieval-Augmented Generation lives under `rag`. `orchestrator.py` acts as the
central router, calling `retriever.py` to search vector memory, `embedder.py` to
create sentence embeddings and `music_oracle.py` to craft musical prompts.

## Entry Points

- `start_dev_agents.py` launches the planner, coder and reviewer agents for a
  development cycle.
- `spiral_os` is a command line utility for deploying YAML-defined pipelines.

## Pipeline Deployment Flow

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as spiral_os
    participant Y as Pipeline YAML
    participant P as Subprocess
    U->>CLI: spiral_os pipeline deploy path.yaml
    CLI->>Y: read steps
    CLI->>P: run step with subprocess
    P-->>CLI: exit code
    CLI-->>U: deployment summary
```

## QNL Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant O as MoGEOrchestrator
    participant Q as qnl_engine
    participant R as rag.retriever
    participant A as audio.engine
    U->>O: text or hex input
    O->>Q: parse_input / hex_to_song
    Q-->>O: tone, glyphs, waveform
    O->>R: query context
    R-->>O: ranked snippets
    O->>A: play or synthesize audio
    A-->>U: WAV file and metadata
```
