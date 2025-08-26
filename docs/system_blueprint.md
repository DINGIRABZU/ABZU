# System Blueprint

## Introduction

The system blueprint acts as the master index for the ABZU platform, summarizing
chakra layers, core services, and operational flows for booting and maintenance.
For high-level orientation, consult:

- [Documentation Index](index.md)
- [Project Overview](project_overview.md)
- [Architecture Overview](architecture_overview.md)
- [Component Index](component_index.md)

For deeper guidance on operations and reliability, refer to:

- [Deployment Guide](deployment.md)
- [Monitoring](monitoring.md)
- [Testing](testing.md)
- [Recovery Playbook](recovery_playbook.md)

## Chakra Layers
- **Root**
  - **Purpose:** I/O and networking foundation managing hardware access and network
    connectivity to anchor the stack.
  - **Heat:** High
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#root)
- **Sacral**
  - **Purpose:** Emotion engine translating sensory input into emotional context that
    guides creative responses.
  - **Heat:** Medium
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#sacral)
- **Solar Plexus**
  - **Purpose:** Learning and state transition layer adapting behavior through
    mutation and retraining cycles.
  - **Heat:** High
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#solar)
- **Heart**
  - **Purpose:** Voice avatar configuration and memory storage anchoring persistent
    knowledge and user personas.
  - **Heat:** Medium
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#heart)
- **Throat**
  - **Purpose:** Prompt orchestration and agent interface linking users to the system
    through gateways and scripts.
  - **Heat:** Medium
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#throat)
- **Third Eye**
  - **Purpose:** Insight, QNL processing, and biosignal narration synthesizing
    perceptions into narrative threads.
  - **Heat:** Low
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#third_eye)
- **Crown**
  - **Purpose:** High-level orchestration coordinating modules and startup rituals.
  - **Heat:** Medium
  - **Links:** [Chakra Overview](chakra_overview.md),
    [Chakra Status](chakra_status.md),
    [Chakra Architecture](chakra_architecture.md),
    [Chakra Koan](chakra_koan_system.md#crown)

## Agents & Nazarick Hierarchy

The ABZU stack relies on a network of Nazarick agents, each aligned with a chakra layer.
Core roles include:

- **Orchestration Master** (Crown) – oversees launch control and high-level coordination. See
  [orchestration_master.py](../orchestration_master.py).
- **Prompt Orchestrator** (Throat) – routes prompts and manages agent interfaces via
  [crown_prompt_orchestrator.py](../crown_prompt_orchestrator.py).
- **QNL Engine** (Third Eye) – performs insight and Quantum Narrative Language processing in
  [SPIRAL_OS/qnl_engine.py](../SPIRAL_OS/qnl_engine.py).
- **Memory Scribe** (Heart) – maintains voice avatar configuration and memory storage using
  [memory_scribe.py](../memory_scribe.py).

Additional Nazarick helpers cover specialized duties such as strategic simulation
([agents/demiurge/strategic_simulator.py](../agents/demiurge/strategic_simulator.py)) and
prompt arbitration ([agents/cocytus/prompt_arbiter.py](../agents/cocytus/prompt_arbiter.py)).
See [nazarick_agents.md](nazarick_agents.md) for the full roster and the
[Component Index](component_index.md) for component explanations.

### Specialized Agents and Orchestrators

- **Vanna Data Agent** – translates natural-language prompts into SQL via the
  `vanna` library and records both results and narrative summaries. Module:
  [`agents/vanna_data.py`](../agents/vanna_data.py), function:
  [`query_db`](../agents/vanna_data.py#L49).
- **GeoKnowledge Graph** – maintains a lightweight geospatial knowledge graph
  using NetworkX with optional GeoPandas support for site and path queries.
  Module: [`agents/land_graph/geo_knowledge.py`](../agents/land_graph/geo_knowledge.py),
  class: `GeoKnowledge`.
- **Albedo Orchestrator** – config-driven development orchestrator that can
  register optional agents like `vanna_data` and `landgraph` through the
  `AGENT_LOOKUP` mapping. Module: [`orchestration_master.py`](../orchestration_master.py),
  class: `AlbedoOrchestrator`.
- **OS Guardian Planner** – LangChain-based planner that sequences perception
  and action tools, storing generated plans in a vector store for reuse.
  Module: [`os_guardian/planning.py`](../os_guardian/planning.py), class:
  `GuardianPlanner`.
- **Development Cycle Orchestrator** – lightweight planner/coder/reviewer loop
  that optionally leverages Microsoft Autogen and vector memory. Module:
  [`tools/dev_orchestrator.py`](../tools/dev_orchestrator.py), classes:
  `Planner`, `Coder`, `Reviewer`, `DevAssistantService`.

## Memory Systems

Inanna AI layers multiple specialized memories that record different facets of
experience. Each store can be queried directly or through a unified search
interface. See [Memory Architecture](memory_architecture.md) for an overview.

- **Cortex Memory** – persistent application state with semantic tag indexes.
  Docs: [Memory Layer](memory_layer.md), [Cortex Search](memory_cortex.md).
  Module: [`memory/cortex.py`](../memory/cortex.py).
- **Emotional Memory** – SQLite log of emotional feature vectors capturing the
  agent's mood. Module: [`memory/emotional.py`](../memory/emotional.py).
- **Mental Memory** – Neo4j-backed task graph with optional reinforcement
  learning hooks. Module: [`memory/mental.py`](../memory/mental.py).
- **Spiritual Memory** – ontology mapping events to symbols for ritual insight.
  Module: [`memory/spiritual.py`](../memory/spiritual.py).
- **Narrative Memory** – story beats linking actors, actions and symbolism.
  Module: [`memory/narrative_engine.py`](../memory/narrative_engine.py).
- **Vector Memory** – FAISS/SQLite text embedding store with decay, snapshots
  and optional Redis backup. Docs: [Vector Memory](vector_memory.md).
  Modules: [`vector_memory.py`](../vector_memory.py),
  [`memory_store.py`](../memory_store.py), [`distributed_memory.py`](../distributed_memory.py).
- **Spiral Memory** – cross-layer event registry that can generate sacred
  glyphs for significant moments. Module: [`spiral_memory.py`](../spiral_memory.py).
- **Spiral Cortex Insights** – JSONL log of retrieval snippets for the spiral
  cortex. Module: [`memory/spiral_cortex.py`](../memory/spiral_cortex.py).
- **Music Memory** – persistent store for music embeddings tagged with emotion.
  Module: [`memory/music_memory.py`](../memory/music_memory.py).
- **Sacred Glyph Memory** – VAE-based generator storing latent vectors and
  images derived from layer embeddings. Module: [`memory/sacred.py`](../memory/sacred.py).
- **Corpus Interaction Log** – rotating log of conversations and ritual
  results. Module: [`corpus_memory_logging.py`](../corpus_memory_logging.py).
- **Unified Memory Search** – aggregates cortex, spiral and vector memories into
  a single result set. Module: [`memory/search.py`](../memory/search.py).

## Essential Services
### Chat Gateway
- **Layer:** Throat
- **Purpose:** Provide the user messaging interface and route requests to internal agents. See [Communication Interfaces](communication_interfaces.md).
- **Startup:** Launch after the memory store is available.
- **Health Check:** Probe `/chat/health` and watch latency.
- **Recovery:** Restart the gateway or verify network configuration.

### Memory Store
- **Layer:** Heart
- **Purpose:** Persist conversations and embeddings for retrieval across sessions. See [Memory Architecture](memory_architecture.md) and [Vector Memory](vector_memory.md).
- **Startup:** Start first to provide persistence for later services.
- **Health Check:** Ping the database and confirm vector index readiness.
- **Recovery:** Restore the database, replay deferred writes, and relaunch.

### Chat2DB Interface
- **Layer:** Heart
- **Purpose:** Bridge the chat gateway with both the SQLite conversation log and the vector memory store.
- **Docs:** [Chat2DB Interface](chat2db.md)
- **Modules:** [`INANNA_AI/db_storage.py`](../INANNA_AI/db_storage.py), [`spiral_vector_db/__init__.py`](../spiral_vector_db/__init__.py)
- **Startup:** Initialize after the memory store is ready.
- **Health Check:** Perform a test read/write against each store.
- **Recovery:** Recreate the database tables or rebuild the vector index.

### CROWN LLM
- **Layer:** Crown
- **Purpose:** Execute high‑level reasoning and language generation. See [CROWN Overview](CROWN_OVERVIEW.md) and [LLM Models](LLM_MODELS.md).
- **Startup:** Initialize once the chat gateway is online and model weights are present.
- **Health Check:** Send a dummy prompt and inspect response time.
- **Recovery:** Reload weights with `crown_model_launcher.sh` or switch to a fallback model.

## Non‑Essential Services
### Audio Device
- **Purpose:** Manage audio capture and playback. See [Audio Ingestion](audio_ingestion.md) and [Voice Setup](voice_setup.md).
- **Startup:** Activate after essential services.
- **Health Check:** Run an audio loopback test.
- **Recovery:** Reinitialize the audio backend or fall back to silent mode.

### Avatar
- **Purpose:** Render the musical persona and drive animations. See [Music Avatar Architecture](music_avatar_architecture.md), [Avatar Pipeline](avatar_pipeline.md), and [Nazarick Agents](nazarick_agents.md).
- **Startup:** Launch after the audio device using Nazarick helpers.
- **Health Check:** Verify avatar frame rendering.
- **Recovery:** Reload avatar assets or restart the pipeline.

### Video
- **Purpose:** Stream generative visuals. See [Video Generation](video_generation.md).
- **Startup:** Final stage.
- **Health Check:** Probe the video stream endpoint.
- **Recovery:** Restart the encoder or disable streaming.

## Staged Startup Order
The stack boots in discrete stages. Deployment scripts or Kubernetes manifests
advance to the next step only after the current service reports a passing
`/ready` check. This sequencing prevents race conditions during rollouts and is
recommended for both local runs and production deployments described in
[deployment.md](deployment.md).

1. Memory Store (Heart)
2. Chat Gateway (Throat)
3. CROWN LLM (Crown)
4. Audio Device
5. Avatar
6. Video

Each step should report readiness before continuing. After the final service
comes online, run the smoke tests in [testing.md](testing.md) to confirm the
system responds as expected.

## Health Checks
Robust health checks keep the system stable and observable.

- Each service exposes `/health` and `/ready` endpoints. Liveness probes confirm
  the process is running, while readiness probes gate traffic until dependencies
  are satisfied.
- `scripts/vast_check.py` aggregates health status across services and feeds
  metrics into the logging and telemetry pipeline outlined in
  [monitoring.md](monitoring.md).
- During deployment, configure these checks so orchestration platforms only
  advance when readiness reports success.

## Failure Scenarios and Recovery Steps
- **Memory store unavailable** – Chat gateway returns 503 or CROWN LLM waits
  indefinitely. Restore from snapshots as outlined in
  [recovery_playbook.md](recovery_playbook.md) and restart from step 1.
- **Chat gateway unhealthy** – `/chat/health` fails due to missing network
  routes or misconfigured credentials. Recheck deployment settings in
  [deployment.md](deployment.md) and redeploy once dependencies respond.
- **CROWN LLM model load failure** – Health probes timeout or responses degrade.
  Reload weights, switch to a fallback model, and validate with prompts from
  [testing.md](testing.md).
- **Non‑essential service stalled** – Avatar or video `/ready` endpoints remain
  false. Inspect logs using the guidance in [monitoring.md](monitoring.md) and
  restart the affected component without disrupting core services.

General guidance: stop the failed service, confirm dependencies, and restart
following the startup order. For persistent issues, consult the
[Recovery Playbook](recovery_playbook.md) to restore from snapshots.

## Contributor Resources

- [Developer Onboarding](developer_onboarding.md)
- [Development Workflow](development_workflow.md)
- [Coding Style](coding_style.md)
