# Reignition

NEOABZU ignites a fresh substrate for ABZU components.

## Goals
- Establish a Rust workspace (`Cargo.toml`) for crates such as `core`, `memory`, and `vector`.
- Prototype computation through a minimal lambda-calculus interpreter with Python bindings.
- Maintain alignment with the architectural vision outlined in [docs/ABZU_blueprint.md](../docs/ABZU_blueprint.md) and
  the operational practices described in [docs/system_blueprint.md](../docs/system_blueprint.md).
- Provide Python helper scaffolding via `pyproject.toml` and isolate testing through a dedicated CI workflow.

This document tracks early milestones as we grow the workspace into a fully fledged system.

## Rust Migration Plan

The migration follows the canonical architecture laid out in the
[Blueprint Spine – Triadic Stack](../docs/blueprint_spine.md#triadic-stack)
and [Blueprint Spine – Memory Bundle](../docs/blueprint_spine.md#memory-bundle).

1. Port deterministic orchestration logic into `neoabzu_core`, aligning with the
   Triadic Stack flow to keep operator → RAZAR → Crown boundaries explicit.
2. Consolidate state layers inside `neoabzu_memory` to mirror the Memory Bundle
   ledger and snapshot cadence.
3. Introduce a `neoabzu_vector` crate that adopts the
   [Nazarick Integration](../docs/blueprint_spine.md#nazarick-integration-with-crown-and-razar)
   scheme for cross-layer queries.
4. Expand crate coverage in step with the
   [Repository Blueprint](../docs/blueprint_spine.md#repository-blueprint) so
   Rust modules remain consistent with documented topology.

These stages keep Python orchestration while progressively shifting stable
computation to Rust.

## Python Orchestration and Rust Dependencies

The orchestration layer remains Python-first, delegating deterministic work to
Rust crates through explicit FFI boundaries:

| Module | Responsibility | Rust dependency | Boundary |
| --- | --- | --- | --- |
| RAZAR orchestrator | boot, recovery, and mission routing | `neoabzu_core`, `neoabzu_memory` | PyO3 |
| FastAPI endpoints (`server.py`, `operator_service/api.py`) | HTTP interfaces for agents and operators | `neoabzu_memory` via PyO3, planned `neoabzu_vector` service | PyO3 / gRPC |

## FFI Contracts

All in-process calls use **PyO3** wrappers:

- `core.evaluate(src: str) -> str`
- `neoabzu_memory.MemoryBundle.initialize() -> Dict[str, str]`
- `neoabzu_memory.MemoryBundle.query(text: str) -> Dict[str, Any]`

Cross-service calls adopt **gRPC**. The upcoming `neoabzu_vector` crate will
offer a `VectorService` with `Init` and `Search` RPCs returning embeddings and
query results.

These boundaries keep orchestration logic in Python while Rust provides
computational stability.

## Vector Service Deployment

Run the gRPC service (binding to `0.0.0.0:50051`) with:

```bash
export NEOABZU_VECTOR_STORE=tests/data/store.json
export NEOABZU_VECTOR_DB=.neoabzu-vector/db
cargo run -p neoabzu-vector --bin server
```

`NEOABZU_VECTOR_STORE` points to a JSON array of seed documents while
`NEOABZU_VECTOR_DB` identifies the persistent sled directory that retains
embeddings across restarts. `Init` embeds the dataset, writes the
records to the database, and reloads from persistence when the JSON seed
is missing. `Search` lazily hydrates in-memory shards from persistent
storage so fresh processes recover without manual bootstrapping.
`NEOABZU_VECTOR_SHARDS` still controls in-memory partitioning for
concurrency; omit or set to `1` for a single shard.

Metrics counters `neoabzu_vector_init_total` and
`neoabzu_vector_search_total` capture call volume, while
`neoabzu_vector_init_latency_seconds` and
`neoabzu_vector_search_latency_seconds` histogram init/search durations.
Launch with `--features tracing` to emit span data and enable `RUST_LOG`
to observe `Init` and `Search` instrumentation. A small command-line
client remains available at `src/bin/vector_client.py` for ad-hoc
queries.

Python callers may connect using `neoabzu.vector.VectorClient`:

```python
from neoabzu.vector import VectorClient

with VectorClient("http://localhost:50051").connect() as client:
    client.init()
    results = client.search("hello", 2)
```

## Contributor Guidelines

Follow [The Absolute Protocol](../docs/The_Absolute_Protocol.md) when committing
changes. Each commit message must state, "I did X on Y to obtain Z, expecting
behavior B," and run `pre-commit run --files <changed files>` before pushing.
