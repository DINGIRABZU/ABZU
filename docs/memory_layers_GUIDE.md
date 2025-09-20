# Memory Layers Guide

**Version:** v1.2.0
**Last updated:** 2025-10-09

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

During ignition, [RAZAR Agent](RAZAR_AGENT.md) invokes `query_memory` once the Rust-backed bundle reports every chakra layer as `ready`. At runtime the [Crown](CROWN_OVERVIEW.md) issues the same call before delegating prompts so active layers provide fresh context as outlined in the [Chakra System Manual](chakra_system_manual.md).

### Broadcasting layer initialization

`MemoryBundle.initialize` wraps `broadcast_layer_event` and emits **one**
`layer_init` mapping for all layers, allowing subscribers to process
initialization in a single step:

```python
from memory.bundle import MemoryBundle

bundle = MemoryBundle()
statuses = bundle.initialize()
diagnostics = bundle.diagnostics
```

The event payload contains a `layers` object populated by the Rust bundle. Each entry is one of three readiness states:

- `ready` – the canonical implementation loaded and responded to the bootstrap probe.
- `skipped` – a Python fallback module was substituted because dependencies are missing.
- `error` – neither the canonical module nor its fallback could initialize.

```json
{
  "layers": {
    "cortex": "ready",
    "emotional": "ready",
    "mental": "skipped",
    "spiritual": "ready",
    "narrative": "error"
  },
  "diagnostics": {
    "failed_attempts": {"narrative": ["neoabzu.memory.narrative.Driver"]},
    "fallbacks": {"mental": "memory.optional.mental_fallback"}
  }
}
```

Clients should treat `ready` layers as active, `skipped` layers as inert no-ops, and `error` layers as failures requiring operator intervention. Stage B readiness reviews also surface the diagnostics payload described below so operators can confirm fallbacks and retry counts before signing off on the boot sequence.

### Diagnostics payload

`MemoryBundle.diagnostics` accompanies the status map on every `layer_init` broadcast. Stage B consumes this object to populate the Prometheus gauges documented in [RAZAR Failover Monitoring](monitoring/RAZAR.md) and to enrich the operations audit trail.

The payload is composed of two keys:

- `failed_attempts` – a mapping of layer names to the fully qualified module paths that failed to initialize.
- `fallbacks` – a mapping of layer names to the fallback module that replaced the canonical implementation.

Layers that initialize without error omit their entry from each map. An example diagnostic envelope looks like this:

```json
{
  "layers": {
    "cortex": "ready",
    "emotional": "ready",
    "mental": "skipped",
    "spiritual": "ready",
    "narrative": "error"
  },
  "diagnostics": {
    "failed_attempts": {
      "narrative": ["neoabzu.memory.narrative.Driver"],
      "mental": ["neoabzu.memory.mental.Driver"]
    },
    "fallbacks": {
      "mental": "memory.optional.mental_fallback"
    }
  }
}
```

The bundle caches the latest diagnostics under `MemoryBundle.diagnostics` so clients can retrieve the data after initialization:

```python
bundle = MemoryBundle()
bundle.initialize()
print(bundle.diagnostics["failed_attempts"])  # {"narrative": ["neoabzu.memory.narrative.Driver"]}
```

Stage B inspectors compare these values with the gauges emitted under the `razar_memory_init_*` namespace to confirm fallbacks and failures were logged.

```mermaid
{{#include figures/layer_init_broadcast.mmd}}
```

The Mermaid source lives at
[figures/layer_init_broadcast.mmd](figures/layer_init_broadcast.mmd).

## Bundle Initialization

`MemoryBundle` wraps the layer modules behind a single interface and reports
their startup state in one event. The Python class is now a thin wrapper over
the Rust `neoabzu_memory` crate, which performs initialization and query
aggregation.

```python
from memory.bundle import MemoryBundle

bundle = MemoryBundle()
statuses = bundle.initialize()
diagnostics = bundle.diagnostics
records = bundle.query("omen")
```

`initialize()` imports each layer and immediately calls
`broadcast_layer_event()` with the resulting status mapping and diagnostics.
During package import every layer attempts to load its implementation and
transparently falls back to the module in `memory.optional` if dependencies
are missing. Substituted layers are marked as `skipped`; initialization
continues and emits a consolidated result regardless of missing components.
When both the canonical module and its fallback fail, the bundle labels the
layer `error` so orchestration services can respond without blocking the
remaining stores. The diagnostics maps record which fallbacks activated and
which imports failed so tooling can reconcile Prometheus gauges with the
bundle event stream.

### Command-line bootstrap

Use the `memory-bootstrap` CLI to initialize the bundle from the command line
and log layer statuses:

```bash
memory-bootstrap
```

Use this during development to verify all layers import correctly. The script
logs `memory_init_duration`, `memory_init_ready`, and `memory_init_failed` in
addition to the layer map, and it writes latency samples to the
`razar_memory_init_duration_seconds` Prometheus gauge exposed alongside
Stage B telemetry.

`razar.boot_orchestrator` records the same metrics when staging the bundle
for production. Every invocation appends the `layers`,
`MemoryBundle.diagnostics`, and the latency counters to the operations log so
prometheus scrapes and Stage B reviewers share a unified view of the boot
sequence.

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

## Unified Broadcast & Query

`broadcast_layer_event` announces layer readiness, while `query_memory` fans out across the same layers to collect results. The combined initialization and query flow looks like this:

```mermaid
{{#include figures/layer_init_query_flow.mmd}}
```

The Mermaid source lives at [figures/layer_init_query_flow.mmd](figures/layer_init_query_flow.mmd).

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
`search_api`, `music_memory`, and `sacred`. When a layer import raises
`ModuleNotFoundError`, initialization automatically loads the matching
fallback, which exposes the same public API but returns empty data structures.
Fallback layers are reported as `skipped`, and calls such as
`aggregate_search` simply yield empty results for them while logging any
underlying errors. If a layer cannot be loaded at all it will be reported as
`error` and omitted from aggregation, while queries continue returning data
from the remaining active layers.

## Tracing

`MemoryBundle` obtains its tracer via ``memory.tracing.get_tracer``, which
reads the ``TRACE_PROVIDER`` environment variable. Set
``TRACE_PROVIDER=opentelemetry`` to emit OpenTelemetry spans, or
``TRACE_PROVIDER=noop`` to disable tracing. Custom tracer factories can be
referenced as ``module.path:function``.

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

Backlinks: [Blueprint Spine](blueprint_spine.md) | [System Blueprint](system_blueprint.md) | [RAZAR Agent](RAZAR_AGENT.md) | [Crown Overview](CROWN_OVERVIEW.md) | [Chakra System Manual](chakra_system_manual.md)
