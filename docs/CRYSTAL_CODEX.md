# CRYSTAL CODEX

## Misión
Spiral OS guides sacred and creative exploration through an emotionally aware AI temple that harmonises music, voice and code. More background lives in [project_overview.md](project_overview.md) and the repository [README](../README.md).

## Arquitectura
The codebase organises modules into seven chakra‑inspired layers that route a request from hardware roots to crown‑level initiation rites. Package responsibilities are mapped in [architecture.md](architecture.md), [architecture_overview.md](architecture_overview.md) and [packages_overview.md](packages_overview.md).

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
Additional request flow diagrams and service contracts live in [architecture_overview.md](architecture_overview.md).

## Dependencias
System packages and Python wheels required for the sonic temple are listed in [dependencies.md](dependencies.md). Core runtime packages include `numpy`, `requests`, `python-json-logger`, `PyYAML` and `psutil`. Versions and licenses are tracked in [dependency-graph.md](dependency-graph.md).

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

## Configuración del entorno
Follow the steps below or see [setup.md](setup.md) for full instructions.

```mermaid
flowchart TD
    A[Clone repository] --> B[Create virtualenv]
    B --> C[pip install .\[llm,audio,ml,vision,web,network\]]
    C --> D[Copy secrets.env.template to secrets.env]
    D --> E[Run scripts/check_requirements.sh]
```

Additional onboarding guides live in [developer_onboarding.md](developer_onboarding.md) and [quick_start_non_technical.md](quick_start_non_technical.md).

## Índice de componentes
For per‑module descriptions and external dependencies see the generated [component_index.md](component_index.md).

## Flujo de desarrollo
Contributors follow a planner–coder–reviewer loop with all changes validated by `pytest`. The cycle and testing guidance are detailed in [development_workflow.md](development_workflow.md).

## Evolución del MVP
El desarrollo del producto mínimo viable avanzó a través de cuatro hitos principales:

1. **Gestor de entorno virtual** – validado ejecutando `scripts/check_requirements.sh`, que confirma la presencia de dependencias del sistema.
2. **Repositorio sandbox** – probado con `pytest --maxfail=1 -q`, con 9 pruebas superadas y 447 omitidas.
3. **Comando `/sandbox`** – verificado en entornos aislados asegurando que los commits se puedan revertir sin efectos colaterales.
4. **Instalador de dependencias** – ejecutado nuevamente `scripts/check_requirements.sh` para garantizar la instalación correcta.

## Notas de lanzamiento
Recent changes removed legacy shims (`qnl_engine.py`, `symbolic_parser.py`) and marked the audio pipeline refresh as complete. Ongoing updates are catalogued in [release_notes.md](release_notes.md).

## Hitos y hoja de ruta
The sovereign voice milestone unified speech synthesis with avatar animation, while **Milestone VIII – Sonic Core & Avatar Expression Harmonics** expanded emotion‑to‑music mapping and WebRTC streaming ([milestone_viii_plan.md](milestone_viii_plan.md)).

```mermaid
mindmap
  root((Roadmap))
    Completed
      "Virtual environment manager"
      "Sandbox repository"
      "/sandbox command"
      "Dependency installer"
      "Rollback runner"
    Upcoming
      "Music command"
      "Avatar lip-sync"
      "Expanded memory search"
      "Voice cloning"
    Future
      "Community Discord channel"
      "New style packs"
      "Hardware scaling strategy"
```

See [roadmap.md](roadmap.md) for the full plan and post‑milestone expansions.

