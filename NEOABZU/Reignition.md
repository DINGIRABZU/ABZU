# Reignition

NEOABZU ignites a fresh substrate for ABZU components.

## Goals
- Establish a Rust workspace (`Cargo.toml`) for crates such as `core`, `memory`, and `vector`.
- Prototype computation through a minimal lambda-calculus interpreter with Python bindings.
- Maintain alignment with the architectural vision outlined in [docs/ABZU_blueprint.md](../docs/ABZU_blueprint.md) and
  the operational practices described in [docs/system_blueprint.md](../docs/system_blueprint.md).
- Provide Python helper scaffolding via `pyproject.toml` and isolate testing through a dedicated CI workflow.

This document tracks early milestones as we grow the workspace into a fully fledged system.

## Python Orchestration and Rust Dependencies

The orchestration layer remains Python-first, delegating deterministic work to
Rust crates through explicit FFI boundaries:

| Module | Responsibility | Rust dependency | Boundary |
| --- | --- | --- | --- |
| RAZAR orchestrator | boot, recovery, and mission routing | `neoabzu_core`, `neoabzu_memory` | PyO3 |
| FastAPI endpoints (`server.py`, `operator_service/api.py`) | HTTP interfaces for agents and operators | `neoabzu_memory` via PyO3, planned `neoabzu_vector` service | PyO3 / gRPC |

## FFI Contracts

All in-process calls use **PyO3** wrappers:

- `neoabzu_core.eval_expr(src: str) -> str`
- `neoabzu_memory.MemoryBundle.initialize() -> Dict[str, str]`
- `neoabzu_memory.MemoryBundle.query(text: str) -> Dict[str, Any]`

Cross-service calls adopt **gRPC**. The upcoming `neoabzu_vector` crate will
offer a `VectorService` with `Init` and `Search` RPCs returning embeddings and
query results.

These boundaries keep orchestration logic in Python while Rust provides
computational stability.
