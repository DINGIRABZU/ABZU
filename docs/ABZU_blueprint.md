# ABZU Blueprint

**Version:** v0.1.0
**Last updated:** 2025-10-05

## Mission & Vision
ABZU ignites inner narratives before external action, weaving memory bundles, dynamic ignition, and operator guidance into a living system that "knows itself" before engaging others [project_mission_vision.md](project_mission_vision.md).

## Guiding Ethos
The project advances inward‑first intelligence, treats narrative as infrastructure, practices embodied co‑learning, preserves chakra balance, ensures portability, and enforces consent‑first ethics [project_mission_vision.md](project_mission_vision.md).

## Macro Architecture

### Memory Bundle
Unified memory layers exchange initialization signals through an event bus, allowing operators to query a consolidated memory spine [memory_layers_GUIDE.md](memory_layers_GUIDE.md).
```mermaid
flowchart TD
    Operator -->|query| MemoryBundle
    MemoryBundle --> Cortex
    MemoryBundle --> Emotional
    MemoryBundle --> Mental
    MemoryBundle --> Spiritual
    MemoryBundle --> Narrative
    Cortex --> MemoryBundle
    Emotional --> MemoryBundle
    Mental --> MemoryBundle
    Spiritual --> MemoryBundle
    Narrative --> MemoryBundle
    MemoryBundle -->|aggregated result| Operator
```

### RAZAR Ignition
RAZAR orchestrates multi-layer boot sequences, prepares environments, launches components, and records mission outcomes for operator oversight [RAZAR_AGENT.md](RAZAR_AGENT.md).
```mermaid
sequenceDiagram
    participant Operator
    participant RAZAR
    participant Components
    Operator->>RAZAR: launch mission
    RAZAR->>RAZAR: parse boot_config
    RAZAR->>Components: ignite sequential
    Components-->>RAZAR: health ok
    RAZAR-->>Operator: report ready
```

### Agent Ecosystem
Chakra-aligned servants coordinate with RAZAR to maintain systemic balance, routing perception and action through the memory bundle and world services [project_mission_vision.md](project_mission_vision.md).
```mermaid
flowchart LR
    Operator --> RAZAR
    RAZAR --> Nazarick[Nazarick Agents]
    Nazarick --> MemoryBundle
    Nazarick --> Worlds
```

### World Replication
Narrative directives drive world engines that render immersive environments and feed telemetry back into the story loop [project_mission_vision.md](project_mission_vision.md).
```mermaid
sequenceDiagram
    participant BANA
    participant WorldEngine
    participant ReplicaWorld
    BANA->>WorldEngine: scene directives
    WorldEngine->>ReplicaWorld: render world
    ReplicaWorld-->>BANA: telemetry
```

## Stepping Stones
- Memory bundle implementation: [memory/bundle.py](../memory/bundle.py)
- Memory bootstrap script: [scripts/bootstrap_memory.py](../scripts/bootstrap_memory.py)
- RAZAR orchestrator: [razar/boot_orchestrator.py](../razar/boot_orchestrator.py)
- Agent roster and roles: [agents/nazarick/nazarick_core_architecture.md](../agents/nazarick/nazarick_core_architecture.md)
- World services scaffold: [worlds/services.py](../worlds/services.py)
- Additional guidance: [RAZAR_AGENT.md](RAZAR_AGENT.md), [memory_layers_GUIDE.md](memory_layers_GUIDE.md), [project_mission_vision.md](project_mission_vision.md)
