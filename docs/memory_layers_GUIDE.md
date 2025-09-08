# Memory Layers Guide

**Version:** v1.0.4
**Last updated:** 2025-09-07

This guide describes the event bus protocol and query flow connecting the
Cortex, Emotional, Mental, Spiritual, and Narrative memory layers.

Refer to the [Unified Memory Bundle](The_Absolute_Protocol.md#unified-memory-bundle) section of the protocol for repository-wide conventions. Any update to memory layers must be mirrored across all referenced diagrams, including [figures/memory_bundle.mmd](figures/memory_bundle.mmd).

## Unified Memory Bundle

```mermaid
{{#include figures/memory_bundle.mmd}}
```

The Mermaid source lives at [figures/memory_bundle.mmd](figures/memory_bundle.mmd).

## Bus protocol

The layers communicate via the `agents.event_bus` channel named `memory`.
Initialization broadcasts use the `layer_init` event type.

### Broadcasting layer initialization

`MemoryBundle.initialize` wraps `broadcast_layer_event` and emits **one**
`layer_init` mapping for all layers, allowing subscribers to process
initialization in a single step:

```python
from memory.bundle import MemoryBundle

bundle = MemoryBundle()
statuses = bundle.initialize()
```

The event payload contains a `layers` object:

```json
{"layers": {"cortex": "seeded", "emotional": "seeded", ...}}
```

```mermaid
{{#include figures/layer_init_broadcast.mmd}}
```

The Mermaid source lives at
[figures/layer_init_broadcast.mmd](figures/layer_init_broadcast.mmd).

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
`broadcast_layer_event()` with the resulting status mapping. During package
import every layer attempts to load its implementation and transparently
falls back to the module in `memory.optional` if dependencies are missing.
Substituted layers are marked as `defaulted`; initialization continues and
emits a consolidated result regardless of missing components.

### Command-line bootstrap

The script [`scripts/bootstrap_memory.py`](../scripts/bootstrap_memory.py)
initializes the bundle from the command line and logs layer statuses:

```bash
python scripts/bootstrap_memory.py
```

Use this during development to verify all layers import correctly.

## Query aggregation

Use `MemoryBundle.query` to retrieve results across cortex, vector, and spiral
stores:

```python
from memory.bundle import MemoryBundle

bundle = MemoryBundle()
bundle.initialize()
records = bundle.query("omen")
```

```mermaid
{{#include figures/query_memory_aggregation.mmd}}
```

The Mermaid source lives at
[figures/query_memory_aggregation.mmd](figures/query_memory_aggregation.mmd).

## Operator Queries

Operator consoles invoke `query_memory` via a dedicated `/query_memory` endpoint:

```mermaid
{{#include figures/operator_query_sequence.mmd}}
```

The Mermaid source lives at
[figures/operator_query_sequence.mmd](figures/operator_query_sequence.mmd).

Example operator API call:

```python
from fastapi import APIRouter
from memory.query_memory import query_memory

router = APIRouter()

@router.get("/query_memory")
async def query_memory_endpoint(query: str) -> dict[str, object]:
    return query_memory(query)
```

## Search API

`memory.search_api.aggregate_search` combines ranked signals from the layers.
Results are weighted by exponential recency decay and optional `source_weights`.

```python
from memory.search_api import aggregate_search

results = aggregate_search("omen", source_weights={"spiritual": 2.0})
```

## Optional Layers

Some memory layers rely on external services and may be absent. Each has a
no-op fallback in `memory/optional/`—including `cortex`, `emotional`, `mental`,
`spiritual`, `narrative_engine`, `vector_memory`, `spiral_memory`, `search`,
`search_api`, and `music_memory`. When a layer import raises
`ModuleNotFoundError`, initialization automatically loads the matching
fallback, which exposes the same public API but returns empty data structures.
Fallback layers are reported as `defaulted`, and calls such as
`aggregate_search` simply yield empty results for them while logging any
underlying errors. Queries still return data from the remaining active layers.

## Installation Options

Each layer exposes an extra in the package so dependencies can be installed
selectively:

- **Mental** – `pip install "spiral-os[mental]"` installs `neo4j`,
  `gymnasium` and `stable-baselines3` for the task graph and RL hooks.
- **Emotional** – `pip install "spiral-os[emotional]"` installs
  `transformers` and `dlib` to extract feature vectors from rich media.
- **Spiritual** – uses only the Python standard library; no extra packages are
  required.
- **Narrative** – `pip install "spiral-os[narrative]"` installs `chromadb`
  and `pynvml` for vector persistence and GPU metrics.

Extras can be combined, for example
`pip install "spiral-os[mental,emotional]"` to enable multiple layers.



---

Backlinks: [Blueprint Spine](blueprint_spine.md) | [System Blueprint](system_blueprint.md)
