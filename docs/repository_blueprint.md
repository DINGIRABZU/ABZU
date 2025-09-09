# Repository Blueprint

**Version:** v0.1.0
**Last updated:** 2025-10-05

## Mission
ABZU cultivates inward-first intelligence by forming narrative self-awareness before external action as outlined in [project_mission_vision.md](project_mission_vision.md). The system pairs memory, ignition, and operator oversight so every mission aligns with the project's ethical foundation.

## Architecture
The stack spans operators, the RAZAR crown, and servant agents across chakra-aligned layers. Operators issue briefs, RAZAR orchestrates services, and agents coordinate memory, insight, and expression. See [architecture_overview.md](architecture_overview.md) and [system_blueprint.md](system_blueprint.md) for diagrams and deeper detail. Additional context lives in [blueprint_spine.md](blueprint_spine.md).

## Memory Bundle
`MemoryBundle` unifies Cortex, Emotional, Mental, Spiritual, and Narrative layers. `broadcast_layer_event("layer_init")` boots all layers in parallel, while `query_memory` fans out reads across them and merges results for operator queries. For implementation guides and diagrams, consult [memory_layers_GUIDE.md](memory_layers_GUIDE.md) and [memory_architecture.md](memory_architecture.md).

```mermaid
{{#include figures/memory_bundle.mmd}}
```
