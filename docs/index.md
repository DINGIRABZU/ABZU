# Documentation Index

Curated starting points for understanding and operating the project. For an exhaustive, auto-generated inventory of all documentation, see [INDEX.md](INDEX.md).

## Orientation
- [ABZU Project Declaration](project_mission_vision.md) – deployments must reach a living state
- [Blueprint Spine](blueprint_spine.md) – mission overview, memory bundle, and ignition map
- [System Blueprint](system_blueprint.md) – chakra layers, dynamic ignition, and operator UI
- [The Absolute Protocol](The_Absolute_Protocol.md) – RAZAR ignition under operator oversight

## Quick Start

Initialize every memory layer with a single command:

```bash
abzu-memory-bootstrap
```

## Memory Bundle
- [Subsystem Overview](ABZU_SUBSYSTEM_OVERVIEW.md#memory-bundle-layers) – full five-layer bundle diagram and roles
- [Memory Layers Guide](memory_layers_GUIDE.md) – bus protocol with diagrams: [Memory Bundle](figures/memory_bundle.mmd), [Layer Initialization Broadcast](figures/layer_init_broadcast.mmd), [Query Memory Aggregation](figures/query_memory_aggregation.mmd)

## Architecture
- [Architecture Overview](architecture_overview.md)
- [Blueprint Export](BLUEPRINT_EXPORT.md) – versioned snapshot of key documents
- [Detailed Architecture](architecture.md)
- [Crown Agent Overview](CROWN_OVERVIEW.md)
## Nazarick
- [Great Tomb of Nazarick](great_tomb_of_nazarick.md)
- [Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md)
- [Nazarick Memory Blueprint](../agents/nazarick/nazarick_memory_blueprint.md)
- [Nazarick Agents](nazarick_agents.md)
- [Nazarick Narrative System](nazarick_narrative_system.md) – maps story events to agents and memory layers
- [Nazarick Manifesto](nazarick_manifesto.md)
- [Nazarick Web Console](nazarick_web_console.md)
- [Operator Protocol](operator_protocol.md)
## Setup
- [Setup Guide](setup.md)
- [Environment Setup](environment_setup.md)
- [Quickstart Setup](setup_quickstart.md) – minimal world configuration
## Usage
- [How to Use](how_to_use.md)
- [UI Service](ui_service.md) – lightweight FastAPI interface for memory queries
- [Operator Console](operator_console.md) – Arcade UI for Operator API commands
- [Arcade UI](arcade_ui.md) – features, env vars, and RAZAR interaction
- [Bootstrap World Script](../scripts/bootstrap_world.py) – populate mandatory layers with defaults

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

## Indices
- [Component Index](component_index.md)
- [Connector Index](connectors/CONNECTOR_INDEX.md)
- [Dependency Index](dependency_index.md)
- [Test Index](test_index.md)
