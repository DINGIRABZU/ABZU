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
- **Root** – I/O and networking foundation that manages hardware access and network
  connectivity. It anchors the stack and brings services online. See
  [Root Chakra Overview](root_chakra_overview.md) and
  [Chakra Architecture](chakra_architecture.md).
- **Sacral** – Emotion engine translating sensory input into emotional context
  that guides creative responses. Refer to [Memory Emotion](memory_emotion.md)
  and [Chakra Architecture](chakra_architecture.md).
- **Solar Plexus** – Learning and state transition layer that adapts behavior
  through mutation and retraining cycles. See [Learning Pipeline](learning_pipeline.md)
  and [Chakra Architecture](chakra_architecture.md).
- **Heart** – Voice avatar configuration and memory storage anchoring persistent
  knowledge and user personas. See [Memory Layer](memory_layer.md) and
  [Chakra Architecture](chakra_architecture.md).
- **Throat** – Prompt orchestration and agent interface linking users to the
  system through gateways and scripts. Refer to
  [Communication Interfaces](communication_interfaces.md) and
  [Chakra Architecture](chakra_architecture.md).
- **Third Eye** – Insight, QNL processing, and biosignal narration synthesizing
  perceptions into narrative threads. See [Insight System](insight_system.md) and
  [Chakra Architecture](chakra_architecture.md).
- **Crown** – High-level orchestration coordinating modules and startup rituals.
  See [CROWN Overview](CROWN_OVERVIEW.md) and
  [Chakra Architecture](chakra_architecture.md).

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
