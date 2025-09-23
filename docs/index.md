# Documentation Index

Curated starting points for understanding and operating the project. For an exhaustive, auto-generated inventory of all documentation, see [INDEX.md](INDEX.md).

## Orientation
- [ABZU Project Declaration](project_mission_vision.md) – deployments must reach a living state
- [Blueprint Spine](blueprint_spine.md) – mission overview, Operator ↔ RAZAR/Crown flow, identity embedding feed, Crown confirms load handshake, identity fingerprint export, identity readiness telemetry, memory bundle, and ignition map
- [System Blueprint](system_blueprint.md) – chakra layers, Operator ↔ RAZAR/Crown flow, identity embedding pipeline, `CROWN_IDENTITY_FINGERPRINT` publishing, `crown_identity_ready` monitoring, handshake enforcement, dynamic ignition, and operator UI
- [gRPC Adoption Milestone](roadmap.md#future-stage--grpc-adoption-milestone) – future-stage scope, triggers, and exit criteria referencing the NeoABZU vector service pattern and Stage gate evidence ledger updates mirrored in the blueprint and Absolute Protocol.
- [Sonic Rehearsal Guide](runbooks/sonic_rehearsal_guide.md) – Stage B audio checklist enforcing `AUDIO_BACKEND=pydub`, FFmpeg/pydub/simpleaudio validation via `python -m audio.check_env --strict`, and the new Ardour/Carla preflight invoked from `scripts/setup_audio_env.sh`.
- [Audio Stack Dependencies](audio_stack.md) – pinned `audio` extras bundle, optional analyzers, and degradation behaviour when packages are absent.
- [Audio Rehearsal Telemetry](monitoring/audio_rehearsal_telemetry.md) – structured logging and archival workflow for Stage B audio metrics.
- [MCP Capability Payload](connectors/mcp_capability_payload.md) – Neo‑APSU connector Stage B handshake schema, rotation metadata, and log expectations.
- [Operator MCP Adoption Audit](connectors/operator_mcp_audit.md) – documents the live Stage B handshake, heartbeat loop, and doctrine checks now wired into `operator_api`/`operator_upload` via `OperatorMCPAdapter`.
- Stage B rehearsal connectors – [operator_api_stage_b.py](../connectors/operator_api_stage_b.py), [operator_upload_stage_b.py](../connectors/operator_upload_stage_b.py), and [crown_handshake_stage_b.py](../connectors/crown_handshake_stage_b.py) wrap the shared helper so rehearsals log credential rotations before adapters serve production traffic.
- [Stage A Automation Endpoints](roadmap.md#stage-a--alpha-gate-confidence) – console buttons invoke `POST /alpha/stage-a1-boot-telemetry`, `/alpha/stage-a2-crown-replays`, and `/alpha/stage-a3-gate-shakeout`, with outputs mirrored under `logs/stage_a/<run_id>/summary.json` for roadmap and doctrine ledgers.
- [Stage C Automation Endpoints](release_runbook.md#stage-c--continuity-planning) – dashboard buttons drive the `/alpha/stage-c1-exit-checklist` through `/alpha/stage-c4-operator-mcp-drill` APIs, logging evidence beneath `logs/stage_c/<run_id>/` for blueprint review.
- [System Overview](system_overview.md) – mission, triadic stack, chakra agents, memory bundle, and avatar stack
- [ABZU Blueprint](ABZU_blueprint.md) – high-level narrative for recreating the system with chakra and heartbeat roles
- [Repository Blueprint](repository_blueprint.md) – mission, architecture, and memory bundle overview
- [The Absolute Protocol](The_Absolute_Protocol.md) – RAZAR ignition under operator oversight with retro console requirements and the architecture change doctrine for synchronizing blueprints and indexes
- [RAZAR Guide](RAZAR_GUIDE.md) – boot orchestration and startup handshakes
- [Crown Guide](Crown_GUIDE.md) – routes operator commands to servant models
- [Nazarick Agents](nazarick_agents.md) – chakra stewards for layer health
- [Narrative Engine Guide](narrative_engine_GUIDE.md) – transforms biosignals into structured StoryEvents
- [Memory Layers Guide](memory_layers_GUIDE.md) – unified bundle and query flow
- [Seeding Crown Memory](project_overview.md#seeding-crown-memory) – corpus scan paths and reindex command

## NEOABZU
NEOABZU explores a Rust-focused substrate while staying aligned with ABZU's core design. Visit [NEOABZU/](../NEOABZU/) for source and [documentation](../NEOABZU/docs/index.md).

## Quick Start

Initialize every memory layer with a single command:

```bash
abzu-memory-bootstrap
```

## Core Architecture

### Memory Bundle
- [ABZU Blueprint – Unified Memory Bundle](ABZU_blueprint.md#unified-memory-bundle) – single bundle gating initialization and unified query
- [System Blueprint – Unified Memory Bundle](system_blueprint.md#memory-bundle) – cross-layer memory flow and spine integration
- [The Absolute Protocol – Unified Memory Bundle](The_Absolute_Protocol.md#unified-memory-bundle) – `layer_init` broadcast and `query_memory` façade
- [Subsystem Overview](ABZU_SUBSYSTEM_OVERVIEW.md#memory-bundle-layers) – full five-layer bundle diagram and roles
- [Memory Layers Guide](memory_layers_GUIDE.md) – bus protocol with diagrams: [Memory Bundle](figures/memory_bundle.mmd), [Layer Initialization Broadcast](figures/layer_init_broadcast.mmd), [Query Memory Aggregation](figures/query_memory_aggregation.mmd)
- [Vector DB Scaling Checklist](scaling/vector_db_scaling_checklist.md) – 10 k-item ingestion drill with P95 latency evidence for standard and fallback pipelines
- [Narrative Engine Guide](narrative_engine_GUIDE.md) – transforms biosignals into structured StoryEvents

### Architecture
- [Architecture Overview](architecture_overview.md)
- [Blueprint Export](BLUEPRINT_EXPORT.md) – versioned snapshot of key documents
- [Detailed Architecture](architecture.md)
- [Crown Agent Overview](CROWN_OVERVIEW.md)
- [RAZAR Guide](RAZAR_GUIDE.md) – boot orchestration and startup handshakes
- [Crown Guide](Crown_GUIDE.md) – routes operator commands to servant models
- [Mission Brief Exchange & Servant Routing](mission_brief_exchange.md) – RAZAR handoff, failure escalation, and servant responses
- [INANNA Guide](INANNA_GUIDE.md) – core GLM interface and memory access
- [Memory Bundle](memory_layers_GUIDE.md) – bus protocol connecting memory layers

## Nazarick
- [Avatar & Voice Stack](blueprint_spine.md#avatar--voice-stack) – servant templates and UI pipeline
- [Nazarick UI Pipeline](system_blueprint.md#avatar--voice-stack) – avatar and voice flow overview
- [Great Tomb of Nazarick](great_tomb_of_nazarick.md)
- [Nazarick Overview](nazarick_overview.md)
- [Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md)
- [Nazarick Memory Blueprint](../agents/nazarick/nazarick_memory_blueprint.md)
- [Nazarick Agents](nazarick_agents.md)
- [Bana Narrative Engine](../nazarick/agents/Bana_narrative_engine.md) – biosignal-driven story generation
- [Nazarick Agents Project Brief](../nazarick/agents/Nazarick_agents_project_brief.md) – agent relationships and narrative dynamics
- [Nazarick Agents Chart](../nazarick/agents/Nazarick_agents_chart.md) – talents and personae of the pantheon
- [System Tear Matrix](../nazarick/agents/system_tear_matrix.md) – hierarchical layer breakdown
- [Nazarick True Ethics](../nazarick/agents/Nazarick_true_ethics.md) – covenant for INANNA_AI
- [Nazarick Narrative System](nazarick_narrative_system.md) – maps story events to agents and memory layers
- [Nazarick Manifesto](nazarick_manifesto.md)
- [Nazarick Web Console](nazarick_web_console.md)
- [Crown vs. Nazarick Modes](nazarick_web_console.md#crown-vs-nazarick-modes) – choose the right interface
- [Operator Protocol](operator_protocol.md)
- [Nazarick Guide](Nazarick_GUIDE.md) – servant orchestration and configuration
- [Albedo Guide](Albedo_GUIDE.md) – personality layer shaping responses
## Setup
- [Setup Guide](setup.md)
- [Environment Setup](environment_setup.md)
- [Quickstart Setup](setup_quickstart.md) – minimal installation and world creation
## Usage
- [How to Use](how_to_use.md)
- [UI Service](ui_service.md) – lightweight FastAPI interface for memory queries
- [Operator Console](operator_console.md) – Arcade UI for Operator API commands
- [Arcade UI](arcade_ui.md) – features, env vars, quickstart, and memory scan sequence
- [Avatar & Voice Stack](avatar_pipeline.md) – end-to-end pipeline and [Arcade Mode Widgets](ui/arcade_mode.md)
- [3D Avatar API](avatar_3d_api.md) – streaming configuration and dependencies
- [Operator Interface Guide](operator_interface_GUIDE.md) – REST endpoints for Crown and RAZAR control
- [Bootstrap World Script](../scripts/bootstrap_world.py) – initialize mandatory layers and report status

## Data
- [Data Manifest](data_manifest.md)
- [DATPars Overview](datpars_overview.md) – goals, architecture, and integration points

## Development
- [The Absolute Protocol](The_Absolute_Protocol.md) (v1.0.98, updated 2025-09-09) – operator interface and retro console requirements
- [Developer Etiquette](developer_etiquette.md)
- [Developer Onboarding](developer_onboarding.md)
- [Development Checklist](development_checklist.md)
- [Documentation Protocol](documentation_protocol.md)
- [Connector Health Protocol](connector_health_protocol.md)
- [Opencode Client](opencode_client.md)
- [Onboarding Guide](onboarding_guide.md) – step-by-step rebuild using docs alone (v1.0.0, updated 2025-08-28)
- [Feature Specifications](features/README.md)
- [Example Feature](features/example_feature.md)
- [RAZAR Agent](RAZAR_AGENT.md)
- [RAZAR Self-Healing Overview](RAZAR_AGENT.md#self-healing-overview)
- [RAZAR rStar Escalation](RAZAR_AGENT.md#rstar-escalation)
- [Security Overview](SECURITY.md#remote-agent-credentials) – rotation cadence
  and sandbox policy for `KIMI2_API_KEY`, `AIRSTAR_API_KEY`, and
  `RSTAR_API_KEY`.
- [Persona API Guide](persona_api_guide.md) – utilities for managing persona interactions

## Indices
- [Component Index](component_index.md)
- [Connector Index](connectors/CONNECTOR_INDEX.md) – lists the doctrine checklist
  for MCP connectors: registry alignment, Stage B heartbeat schema validation,
  and credential rotation freshness.
- [Dependency Index](dependency_index.md)
- [Test Index](test_index.md)
