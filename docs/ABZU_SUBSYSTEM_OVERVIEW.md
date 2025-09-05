# ABZU Subsystem Overview

The diagram below outlines how the primary subsystems collaborate within ABZU.

```mermaid
graph TD
    UI[User Interface] --> Persona[Persona API]
    Persona --> Crown[Crown Router]
    Crown --> RAG[RAG Orchestrator]
    Crown --> Insight[Insight Engine]
    Insight --> Persona
    RAG --> Data[External Data Sources]

    RAG --> Query
    subgraph Memory_Bundle[Memory Bundle]
        direction TB
        layer_init{{layer_init}}
        layer_init --> Cortex
        layer_init --> Emotional
        layer_init --> Mental
        layer_init --> Spiritual
        layer_init --> Narrative

        Query --> Cortex
        Query --> Emotional
        Query --> Mental
        Query --> Spiritual
        Query --> Narrative

        Cortex --> Aggregate
        Emotional --> Aggregate
        Mental --> Aggregate
        Spiritual --> Aggregate
        Narrative --> Aggregate
    end
    Aggregate --> RAG
```

**User Interface → Persona API**
: User intents enter through the interface and are normalized by the Persona API.

**Persona API → Crown Router**
: The Persona API forwards structured requests to the Crown Router, which coordinates system-level actions.

**Crown Router → RAG Orchestrator**
: When knowledge retrieval is required, the Crown Router invokes the RAG Orchestrator to gather context.

**RAG Orchestrator → Memory Bundle**
: The RAG layer dispatches queries to the unified memory bundle, which spans the Cortex, Emotional, Mental, Spiritual, and Narrative layers.

**RAG Orchestrator → External Data Sources**
: If additional information is needed, the RAG layer reaches out to external connectors (see [Connector Index](connectors/CONNECTOR_INDEX.md)).

**Crown Router → Insight Engine**
: For higher-order reasoning over the collected context, the Crown Router engages the Insight Engine.

**Insight Engine → Persona API**
: Synthesized insights flow back through the Persona API before returning to the user.

- **Bundle initialization** – `MemoryBundle.initialize()` emits a single `layer_init` broadcast, seeding all five layers at once.
- **Query traversal** – `MemoryBundle.query()` fans requests across every layer and aggregates the responses before returning to the RAG Orchestrator.
- See [Memory Layers Guide](memory_layers_GUIDE.md) for implementation specifics.
