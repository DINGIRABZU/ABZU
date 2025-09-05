# Memory Layers Guide

This guide describes the event bus protocol and query flow connecting the
Cortex, Emotional, Mental, Spiritual, and Narrative memory layers.

## Bus protocol

The layers communicate via the `agents.event_bus` channel named `memory`.
Initialization broadcasts use the `layer_init` event type.

### Broadcasting layer initialization

`broadcast_layer_event` now emits **one** event containing a mapping for all
layers, allowing subscribers to process initialization in a single step.

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

The payload contains a `layers` object:

```json
{"layers": {"cortex": "seeded", "emotional": "seeded", ...}}
```

## Bundle Initialization

`MemoryBundle` wraps the layer modules behind a single interface and reports
their startup state in one event.

```python
from memory.bundle import MemoryBundle

bundle = MemoryBundle()
statuses = bundle.initialize()
records = bundle.query("omen")
```

`initialize()` imports each layer and immediately calls
`broadcast_layer_event()` with the resulting status mapping. When the optional
mental layer or its dependencies are missing, the bundle substitutes the
no-op implementation from `memory.optional.mental` and marks the status as
`defaulted`. Any other import error is reported as `error`, but initialization
continues and emits a consolidated result.

## Query aggregation

Use `memory.query_memory.query_memory` to retrieve results across cortex,
vector, and spiral stores:

```python
from memory import query_memory

records = query_memory("omen")
```

## Search API

`memory.search_api.aggregate_search` combines ranked signals from the layers.
Results are weighted by exponential recency decay and optional `source_weights`.

```python
from memory.search_api import aggregate_search

results = aggregate_search("omen", source_weights={"spiritual": 2.0})
```

## Optional Layers

Some memory layers rely on external services and may be absent. When a layer
fails to import, the system substitutes a no-op implementation from
`memory/optional/` with the same public API. Initialization marks these
substituted layers as `defaulted`, and calls such as `aggregate_search` simply
yield empty results for them while logging any underlying errors. Queries still
return data from the remaining active layers.


