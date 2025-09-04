# Memory Layers Guide

This guide describes the event bus protocol connecting the Cortex, Emotional,
Mental, Spiritual, and Narrative memory layers.

## Bus protocol

The layers communicate via the `agents.event_bus` channel named `memory`.
Initialization broadcasts use the `layer_init` event type.

### Broadcasting layer initialization

```python
from memory import broadcast_layer_event

broadcast_layer_event({
    "cortex": "seeded",
    "emotional": "seeded",
    "mental": "skipped",
    "spiritual": "seeded",
    "narrative": "seeded",
})
```

Each emitted event carries a payload:

```json
{"layer": "<layer_name>", "status": "<status>"}
```

Subscribers listen on the `memory` channel to react when individual layers
initialize or change state.

## Search API

Use `memory.search_api.aggregate_search` to query across these layers. Results
are ranked by exponential recency decay and can be weighted per source through
`source_weights`.

```python
from memory.search_api import aggregate_search

results = aggregate_search("omen", source_weights={"spiritual": 2.0})
```


