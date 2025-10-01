# APSU Migration Matrix

This matrix consolidates the status of legacy APSU entry points and their Neo-APSU counterparts. Each row lists the legacy module, the Rust crate or PyO3 bridge replacing it, the current migration state, and known defects recorded in readiness packets or doctrine logs. The machine-readable representation lives in `component_index.json` under `apsu_migration`.

| Legacy Entry Point | Neo-APSU Module / Crate | Status | Known Defects / Evidence |
| --- | --- | --- | --- |
| `crown_router` | `neoabzu_crown` | Ported | Rust parity suites cover the routing bridge and retired Python implementation; no open defects recorded.【F:NEOABZU/docs/migration_crosswalk.md†L11-L24】【F:docs/system_blueprint.md†L544-L552】 |
| `identity_loader.py` | `neoabzu_crown::load_identity` | Ported | PyO3 bridge promotes Crown identity synthesis at boot with parity against the legacy loader; no defects reported in readiness bundles.【F:NEOABZU/docs/migration_crosswalk.md†L11-L24】【F:init_crown_agent.py†L21-L44】 |
| `crown_decider.py` | `neoabzu_crown::route_decision` | Pending rewrite | Stage C readiness used the sandbox stub, blocking MoGE orchestrator parity until Stage D wires the Rust engine and validator gating.【F:docs/PROJECT_STATUS.md†L180-L187】 |
| `crown_prompt_orchestrator.py` | `neoabzu_rag::MoGEOrchestrator` | Pending rewrite | Async pipeline remained stubbed in Stage C evidence; Stage D must route traffic through the Rust orchestrator to log retrieval telemetry.【F:docs/PROJECT_STATUS.md†L182-L187】 |
| `state_transition_engine.py` | `neoabzu_crown::route_inevitability` | Pending rewrite | Deterministic sandbox rotations left ritual gating untested; migration depends on emitting inevitability journeys from the Rust bridge.【F:docs/PROJECT_STATUS.md†L182-L187】 |
| `servant_model_manager.py` | `neoabzu_crown` servant bridge | Pending rewrite | Sandbox runs hid servant telemetry behind the local registry stub; Stage D must adopt the Rust-managed registry for contract evidence.【F:docs/PROJECT_STATUS.md†L182-L187】 |
| `emotional_state.py` | `neoabzu_crown` expression pipeline | Pending rewrite | In-memory shim suppressed persisted aura updates; Rust expression telemetry must replace the sandbox path before Stage D exit.【F:docs/PROJECT_STATUS.md†L182-L187】 |
| `memory_store.py` | `neoabzu_memory::MemoryBundle` | Wrapped | Stage C readiness logged `cortex layer empty`, forcing optional memory stubs until Rust persistence closes the gap.【F:docs/PROJECT_STATUS.md†L186-L187】【F:logs/stage_c/20250927T201020Z-stage_c3_readiness_sync/summary.json†L590-L627】 |
| `connectors/operator_mcp_adapter.py` | REST↔gRPC transport via `operator_api`/`operator_api_grpc` | Wrapped | Transport parity achieved in sandbox, but hardware telemetry and heartbeat metrics remain deferred in Stage D/E risk logs.【F:docs/PROJECT_STATUS.md†L174-L205】 |

## Usage

- Update this table and the `apsu_migration` array whenever migration status changes, including defect references and readiness evidence.
- Contract tests for ported rows live under `tests/apsu_migration/` to compare legacy Python behavior with PyO3 shims in a sandbox-safe manner.

## Related Artifacts

- [Migration Crosswalk](../NEOABZU/docs/migration_crosswalk.md)
- [System Blueprint](system_blueprint.md)
- [Project Status – Stage D backlog](PROJECT_STATUS.md#stage-d-bridge-snapshot)
