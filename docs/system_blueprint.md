# System Blueprint

## Introduction

The system blueprint acts as the master index for the ABZU platform, summarizing chakra layers, core services, and operational flows for booting and maintenance. For high-level orientation, consult:

- [Documentation Index](index.md)
- [Project Overview](project_overview.md)
- [Architecture Overview](architecture_overview.md)
- [Component Index](component_index.md)
- [Recovery Playbook](recovery_playbook.md)

## Chakra Layers
- **Root** – I/O and networking foundation
- **Sacral** – Emotion engine
- **Solar Plexus** – Learning and state transitions
- **Heart** – Voice avatar configuration and memory storage
- **Throat** – Prompt orchestration and agent interface
- **Third Eye** – Insight, QNL processing, biosignal narration
- **Crown** – High-level orchestration; see [CROWN Overview](CROWN_OVERVIEW.md)

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
