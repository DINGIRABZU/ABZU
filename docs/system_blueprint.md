# System Blueprint

## Introduction

The system blueprint acts as the master index for the ABZU platform, summarizing chakra layers, core services, and operational flows for booting and maintenance. For high-level orientation, consult:

- [Documentation Index](index.md)
- [Project Overview](project_overview.md)
- [Architecture Overview](architecture_overview.md)
- [Component Index](component_index.md)
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
- **Startup:** Launch after the memory store is available.
- **Health Check:** Probe `/chat/health` and watch latency.
- **Recovery:** Restart the gateway or verify network configuration.

### Memory Store
- **Layer:** Heart
- **Startup:** Start first to provide persistence for later services.
- **Health Check:** Ping the database and confirm vector index readiness.
- **Recovery:** Restore the database, replay deferred writes, and relaunch.

### CROWN LLM
- **Layer:** Crown
- **Startup:** Initialize once the chat gateway is online and model weights are present.
- **Health Check:** Send a dummy prompt and inspect response time.
- **Recovery:** Reload weights with `crown_model_launcher.sh` or switch to a fallback model. See [CROWN Overview](CROWN_OVERVIEW.md).

## Non‑Essential Services
### Audio Device
- **Startup:** Activate after essential services.
- **Health Check:** Run an audio loopback test.
- **Recovery:** Reinitialize the audio backend or fall back to silent mode.

### Avatar
- **Startup:** Launch after the audio device using Nazarick helpers.
- **Health Check:** Verify avatar frame rendering.
- **Recovery:** Reload avatar assets or restart the pipeline. Related agents are cataloged in [Nazarick Agents](nazarick_agents.md).

### Video
- **Startup:** Final stage.
- **Health Check:** Probe the video stream endpoint.
- **Recovery:** Restart the encoder or disable streaming.

## Staged Startup Order
1. Memory Store (Heart)
2. Chat Gateway (Throat)
3. CROWN LLM (Crown)
4. Audio Device
5. Avatar
6. Video

## Health Checks
- Each service exposes `/health` and `/ready` endpoints.
- `scripts/vast_check.py` aggregates health status across services.

## Recovery Paths
- Stop the failed service, confirm dependencies, and restart following the startup order.
- For persistent issues, consult `docs/recovery_playbook.md` to restore from snapshots.
