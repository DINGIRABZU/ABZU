# CRYSTAL CODEX

The codex gathers the mission, dependency matrix, component index,
memory and learning architecture, and self‑improvement protocols. It
cross‑links modules and APIs so contributors can navigate the sonic
temple. Reference guides include
[architecture_overview.md](architecture_overview.md),
[component_index.md](component_index.md),
[api_reference.md](api_reference.md) and [setup.md](setup.md).
Quality ratings for key components are tracked in
[QUALITY_EVALUATION.md](QUALITY_EVALUATION.md).

## Mission
Spiral OS guides sacred and creative exploration through an emotionally aware
AI temple that harmonises music, voice and code. More background lives in
[project_overview.md](project_overview.md) and the repository
[README](../README.md).

## Architecture
The codebase organises modules into seven chakra‑inspired layers that
route a request from hardware roots to crown‑level initiation rites.
Package responsibilities are mapped in
[architecture.md](architecture.md),
[architecture_overview.md](architecture_overview.md) and
[packages_overview.md](packages_overview.md).

### Module Interactions
```mermaid
graph TD
    subgraph Core
        Router
        EA[Emotion Analyzer]
        MS[Model Selector]
        ML[Memory Logger]
    end
    Router --> EA --> MS --> ML
    ML -->|persist| memory[(Memory Stores)]
```
Additional request flow diagrams and service contracts live in
[architecture_overview.md](architecture_overview.md).

## Dependencies and Optional Extras
System packages and Python wheels required for the sonic temple are listed in
[dependencies.md](dependencies.md). Core runtime packages include `numpy`,
`requests`, `python-json-logger`, `PyYAML` and `psutil`. Versions and licenses
are tracked in [dependency-graph.md](dependency-graph.md).

| Paquete            | Propósito                         |
|--------------------|-----------------------------------|
| numpy              | Operaciones numéricas             |
| requests           | Peticiones HTTP                   |
| python-json-logger | Formato de registros estructurados|
| PyYAML             | Carga de configuración YAML       |
| psutil             | Métricas del sistema              |

```mermaid
graph LR
    Spiral_OS --> numpy
    Spiral_OS --> requests
    requests --> urllib3
    requests --> certifi
    requests --> idna
    requests --> charset_normalizer
    Spiral_OS --> python_json_logger
    Spiral_OS --> PyYAML
    Spiral_OS --> psutil
```

### Optional dependency groups
Extras in [pyproject.toml](../pyproject.toml) enable specialised features such
as language models, audio processing and web APIs. Install any combination with
`pip install .[group]` where `group` is one or more of【F:pyproject.toml†L24-L103】:

- `llm` – large language model interfaces
- `audio` – transcription and signal tools
- `ml` – experiment tracking and vector search
- `vision` – screen capture and OCR helpers
- `web` – FastAPI, Streamlit and scraping utilities
- `network` – packet capture and analysis
- `extras` – reinforcement learning and avatar generation
- `dev` – testing and formatting suites

## Configuración del entorno
Follow the steps below or see [setup.md](setup.md) for full instructions.

```mermaid
flowchart TD
    A[Clone repository] --> B[Create virtualenv]
    B --> C[pip install .\[llm,audio,ml,vision,web,network\]]
    C --> D[Copy secrets.env.template to secrets.env]
    D --> E[Run scripts/check_requirements.sh]
```

Additional onboarding guides live in
[developer_onboarding.md](developer_onboarding.md) and
[quick_start_non_technical.md](quick_start_non_technical.md).

## Package Roles
For per‑module descriptions and external dependencies see the generated
[component_index.md](component_index.md). API routes are documented in
[api_reference.md](api_reference.md). Notable modules include
[server.py](../server.py), [vector_memory.py](../vector_memory.py) and
[learning_mutator.py](../learning_mutator.py).

## Agent Instructions

### INANNA_AI
The command line agent assembles activation chants or QNL songs from source
texts. Usage options include `--activate`, `--hex`, `--list` and an interactive
`chat` mode【F:AGENTS.md†L8-L21】.

### Preflight
`tools/preflight.py` validates environment variables, Python packages and
required binaries. Run it with `python tools/preflight.py` or append
`--report` for a JSON summary of issues【F:tools/preflight.py†L3-L45】.

### Watchdog
`monitoring/watchdog.py` monitors CPU, memory and file descriptors for selected
services. Alerts are logged and optional Prometheus metrics are exposed. Launch
it with `python monitoring/watchdog.py`【F:monitoring/README.md†L12-L23】.

### Triage
Investigate failing tests using development agents by running
`start_dev_agents.py --triage <pytest paths>`. Results are saved to
`logs/triage_<timestamp>.log` and transcripts under
`data/triage_sessions/`【F:docs/operations.md†L25-L37】.

## Arquitectura de memoria y aprendizaje
Memory flows from the spiral cortex into a vector database and back
through learning helpers. The layers are described in
[memory_architecture.md](memory_architecture.md) and implemented by
[spiral_memory.py](../spiral_memory.py),
[vector_memory.py](../vector_memory.py) and
[insight_compiler.py](../insight_compiler.py).

```mermaid
flowchart LR
    Input[User Input] --> Cortex[Spiral Cortex]
    Cortex --> VectorDB[(Vector DB)]
    VectorDB --> Compiler[insight_compiler.py]
    Compiler --> Mutator[learning_mutator.py]
    Mutator --> Auto[auto_retrain.py]
    Auto --> Cortex
```

Memory operations are exposed through the API endpoints listed in
[api_reference.md](api_reference.md#memory).

## Protocolos de auto‑mejora
The system refines itself through scheduled scripts and feedback loops:

- [archetype_feedback_loop.py](../archetype_feedback_loop.py) balances
  persona layers.
- [learning_mutator.py](../learning_mutator.py) proposes prompt
  mutations based on insight statistics.
- [auto_retrain.py](../auto_retrain.py) applies approved changes.
- [psychic_loop.md](psychic_loop.md) outlines the reflection cycle.

Training endpoints are documented in
[api_reference.md](api_reference.md#training).

## Pipelines de avatar y voz
Text responses traverse the voice stack and animate the avatar before
streaming to the client. Pipeline details live in
[avatar_pipeline.md](avatar_pipeline.md) and
[voice_aura.md](voice_aura.md).

```mermaid
flowchart LR
    Text --> TTS[Text-to-Speech]
    TTS --> VC[Voice Conversion]
    VC --> Avatar[Avatar Animation]
    Avatar --> Stream[WebRTC Stream]
```

Implementation modules: [music_generation.py](../music_generation.py),
[video_stream.py](../video_stream.py) and
[voice_avatar_config.yaml](../voice_avatar_config.yaml).

## Flujo de desarrollo
Contributors follow a planner–coder–reviewer loop with all changes validated by
`pytest`. The cycle and testing guidance are detailed in
[development_workflow.md](development_workflow.md).

```mermaid
flowchart LR
    Plan --> Code --> Review --> Plan
```

## Progreso de hitos
Seven milestones guide development. Completed items are checked below.

```mermaid
timeline
    title Milestones
    1 : Virtual environment manager
    2 : Sandbox repository
    3 : /sandbox command
    4 : Dependency installer
    5 : Music command
    6 : Avatar lip-sync
    7 : Expanded memory search
```

| # | Hito                      | Estado      |
|---|---------------------------|-------------|
|1|Virtual environment manager|✅ Completo|
|2|Sandbox repository|✅ Completo|
|3|/sandbox command|✅ Completo|
|4|Dependency installer|✅ Completo|
|5|Music command|En progreso|
|6|Avatar lip-sync|Planificado|
|7|Expanded memory search|Planificado|

See [roadmap.md](roadmap.md) and [milestone_viii_plan.md](milestone_viii_plan.md)
for expanded plans.

## Mejoras recientes

| Métrica              | Antes                       | Después                     |
|----------------------|-----------------------------|-----------------------------|
| Advertencias linter  | 42                           | 0                           |
| Dependencias obsoletas| 15 paquetes sin uso         | Paquetes depurados y fijados|
| Cobertura de pruebas | 65%                          | 85%                         |


## Release Notes
Recent changes are captured in [release_notes.md](release_notes.md). Highlights
include removal of legacy compatibility shims and milestone status updates【F:docs/release_notes.md†L1-L7】.

## Roadmap
Upcoming agent enhancements focus on music generation, avatar lip‑sync and
expanded memory search. Longer‑term plans include community coordination, new
style packs and hardware scaling【F:docs/roadmap.md†L15-L25】.

