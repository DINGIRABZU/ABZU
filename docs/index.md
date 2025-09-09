# Documentation Index

Curated starting points for understanding and operating the project. For an exhaustive, auto-generated inventory of all documentation, see [INDEX.md](INDEX.md).

## Orientation
- [ABZU Project Declaration](project_mission_vision.md) – deployments must reach a living state
- [Blueprint Spine](blueprint_spine.md) – mission overview, memory bundle, and ignition map
- [System Blueprint](system_blueprint.md) – chakra layers, dynamic ignition, and operator UI
- [ABZU Blueprint](ABZU_blueprint.md) – high-level narrative for recreating the system with chakra and heartbeat roles
- [Repository Blueprint](repository_blueprint.md) – mission, architecture, and memory bundle overview
- [The Absolute Protocol](The_Absolute_Protocol.md) – RAZAR ignition under operator oversight

## Quick Start

Initialize every memory layer with a single command:

```bash
abzu-memory-bootstrap
```

## Memory Bundle
- [The Absolute Protocol – Unified Memory Bundle](The_Absolute_Protocol.md#unified-memory-bundle) – `layer_init` broadcast and `query_memory` façade
- [Subsystem Overview](ABZU_SUBSYSTEM_OVERVIEW.md#memory-bundle-layers) – full five-layer bundle diagram and roles
- [Memory Layers Guide](memory_layers_GUIDE.md) – bus protocol with diagrams: [Memory Bundle](figures/memory_bundle.mmd), [Layer Initialization Broadcast](figures/layer_init_broadcast.mmd), [Query Memory Aggregation](figures/query_memory_aggregation.mmd)
- [Narrative Engine Guide](narrative_engine_GUIDE.md) – transforms biosignals into structured StoryEvents

## Architecture
- [Architecture Overview](architecture_overview.md)
- [Blueprint Export](BLUEPRINT_EXPORT.md) – versioned snapshot of key documents
- [Detailed Architecture](architecture.md)
- [Crown Agent Overview](CROWN_OVERVIEW.md)
- [RAZAR Guide](RAZAR_GUIDE.md) – boot orchestration and startup handshakes
- [Crown Guide](Crown_GUIDE.md) – routes operator commands to servant models
- [INANNA Guide](INANNA_GUIDE.md) – core GLM interface and memory access
- [Memory Bundle](memory_layers_GUIDE.md) – bus protocol connecting memory layers
## Nazarick
- [Avatar & Voice Stack](blueprint_spine.md#avatar--voice-stack) – servant templates and UI pipeline
- [Nazarick UI Pipeline](system_blueprint.md#avatar--voice-stack) – avatar and voice flow overview
- [Great Tomb of Nazarick](great_tomb_of_nazarick.md)
- [Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md)
- [Nazarick Memory Blueprint](../agents/nazarick/nazarick_memory_blueprint.md)
- [Nazarick Agents](nazarick_agents.md)
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
- [Operator Interface Guide](operator_interface_GUIDE.md) – REST endpoints for Crown and RAZAR control
- [Bootstrap World Script](../scripts/bootstrap_world.py) – initialize mandatory layers and report status

## Data
- [Data Manifest](data_manifest.md)

## Development
- [The Absolute Protocol](The_Absolute_Protocol.md) (v1.0.96, updated 2025-10-05)
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
- [Persona API Guide](persona_api_guide.md) – utilities for managing persona interactions

## Indices
- [Component Index](component_index.md)
- [Connector Index](connectors/CONNECTOR_INDEX.md)
- [Dependency Index](dependency_index.md)
- [Test Index](test_index.md)
