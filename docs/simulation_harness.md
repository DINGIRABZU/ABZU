# Codex Simulation Harness for APSU Migrations

This playbook explains how to exercise legacy Python APSU modules and their Neo-APSU counterparts inside the Codex sandbox. It clarifies harness inputs, where to locate fixtures and stubs, which logs confirm success, and how each drill aligns with the APSU migration matrix so reviewers know which behaviors remain hardware-only.

## Harness scope and prerequisites

- **Workspace.** Run all commands from the repository root so relative paths to fixtures and migration stubs resolve correctly.
- **Environment.** Activate the Codex documentation environment and install test dependencies listed in `requirements.txt` before invoking module-specific harnesses.
- **Logging.** Point the `logs/` directory to a writable sandbox path. Each module drill captures structured JSON under `logs/simulation_harness/<module>/` so parity reviewers can diff the artifacts against readiness packets.
- **Reference index.** Keep the [APSU migration matrix](apsu_migration_matrix.md) open while running drills; every module checklist below cites the exact row for fixture lookups and hardware deferrals.【F:docs/apsu_migration_matrix.md†L5-L15】

## Module drills

### `crown_router`

- **Inputs.** Provide a transcript payload (`text`, `emotion`) plus pre-recorded vector memory rows. The harness seeds deterministic memory entries using `tests/crown/test_router_memory.py::test_expression_memory_influences_choice` to mirror both legacy and PyO3 paths.【F:tests/crown/test_router_memory.py†L48-L91】
- **Execution.** Import `crown_router` and re-run `route_decision` twice: once with the legacy Python module, once with the PyO3 export surfaced by `neoabzu_crown::route_decision` per the migration matrix.【F:docs/apsu_migration_matrix.md†L5-L8】
- **Expected logs.** Success yields `expression_decision` records showing the memory override in the sandbox log bundle (`logs/simulation_harness/crown_router/*.json`). Entries must include `tts_backend`, `avatar_style`, and `soul_state` parity fields.
- **Success criteria.** Both runs choose the same backend and avatar style and emit matching vector-memory hashes.

### `identity_loader.py`

- **Inputs.** Generate mission, persona, and doctrine snippets under a temporary directory mirroring `tests/apsu_migration/test_identity_loader_parity.py` fixtures.【F:tests/apsu_migration/test_identity_loader_parity.py†L35-L115】
- **Execution.** Call `identity_loader.load_identity` with a fake GLM integration, then run the PyO3 stub referenced in the migration matrix (`neoabzu_crown::load_identity`).【F:docs/apsu_migration_matrix.md†L8-L8】
- **Expected logs.** The harness stores `identity.json`, embedded vector payloads, and insight updates. Log records include handshake prompts and the resulting `CROWN-IDENTITY-ACK` token.
- **Success criteria.** Legacy and Neo-APSU runs produce identical summaries, identical GLM prompt call sequences, and matching fingerprint telemetry files.

### `crown_decider.py`

- **Inputs.** Stub servant listings, affect scoring, and emotional memory responses using the patterns from `tests/crown/test_decider.py`.【F:tests/crown/test_decider.py†L26-L74】
- **Execution.** Run the legacy `recommend_llm` flow and compare it against the PyO3-backed `neoabzu_crown::route_decision` exposure scheduled in the migration matrix.【F:docs/apsu_migration_matrix.md†L9-L9】
- **Expected logs.** Capture decision payloads in `logs/simulation_harness/crown_decider/decision.json`, including chosen model, affect scores, and memory provenance metadata.
- **Success criteria.** The sandbox stub and Rust bridge agree on the recommended LLM for identical affect inputs. Any divergence is tagged `environment-limited` pending Stage F hardware validation.

### `crown_prompt_orchestrator.py`

- **Inputs.** Provide interaction history seeds, servant handlers, and optional memory fetchers mirroring `tests/crown/test_prompt_orchestrator.py` fixtures.【F:tests/crown/test_prompt_orchestrator.py†L44-L156】
- **Execution.** Run `crown_prompt_orchestrator_async` with both GLM and servant targets, then exercise the PyO3 orchestrator declared in the migration matrix (`neoabzu_rag::MoGEOrchestrator`).【F:docs/apsu_migration_matrix.md†L10-L10】
- **Expected logs.** Persist request/response transcripts, servant routing decisions, and fallback reasons. Flag memory retrieval failures with structured `environment-limited` annotations for parity auditors.
- **Success criteria.** Sandbox drill records consistent servant selection, fallbacks, and ritual state transitions across legacy and Neo implementations.

### `state_transition_engine.py`

- **Inputs.** Use the minimal state progression phrases from `tests/test_state_transition_engine.py`.【F:tests/test_state_transition_engine.py†L14-L20】
- **Execution.** Instantiate `StateTransitionEngine` and replay the phrase sequence through both the Python implementation and the Neo inevitability tracer described in the migration matrix (`neoabzu_crown::route_inevitability`).【F:docs/apsu_migration_matrix.md†L11-L11】
- **Expected logs.** Emit state timeline events with timestamps and source markers (legacy vs Neo) for Stage replay bundles.
- **Success criteria.** The state machine enters `dormant → active → ritual` in the same order for both paths, with no dropped transitions.

### `servant_model_manager.py`

- **Inputs.** Register coroutine and subprocess servants following `tests/test_servant_model_manager.py`.【F:tests/test_servant_model_manager.py†L19-L36】
- **Execution.** Invoke `register_model`, `invoke`, and `invoke_sync` along with the Neo servant lifecycle bridge planned in the migration matrix entry.【F:docs/apsu_migration_matrix.md†L12-L12】
- **Expected logs.** Capture servant registrations, invocation latencies, and exception traces for fallback drills.
- **Success criteria.** Legacy registry and Neo bridge accept identical registrations, return the same payloads, and record consistent latency metrics.

### `emotional_state.py`

- **Inputs.** Redirect persistence files to a sandbox directory and run concurrent emotion updates per `tests/test_emotion_state.py`.【F:tests/test_emotion_state.py†L18-L62】
- **Execution.** Exercise `set_last_emotion`, `set_current_layer`, and registry persistence, then evaluate the Neo crown expression pipeline hooks highlighted in the migration matrix.【F:docs/apsu_migration_matrix.md†L13-L13】
- **Expected logs.** Produce `state.json`, `registry.json`, and event logs capturing aura telemetry placeholders and identifying synthetic spans.
- **Success criteria.** Both implementations persist identical emotion states and registry contents. Differences in telemetry fidelity are annotated as hardware-only gaps.

### `memory_store.py`

- **Inputs.** Provide FAISS substitutes and SQLite shims following `tests/test_memory_store.py`.【F:tests/test_memory_store.py†L12-L93】
- **Execution.** Run `add`, `search`, `rewrite`, `snapshot`, and `restore`, then replay the same sequence through the Neo `MemoryBundle` export described in the migration matrix.【F:docs/apsu_migration_matrix.md†L14-L14】
- **Expected logs.** Snapshot reports enumerate inserted vector IDs, metadata payloads, and checksum results. When the FAISS shim is active, log the `environment-limited` indicator from the migration matrix notes.
- **Success criteria.** Legacy and Neo executions return the same search ordering, metadata, and snapshot hashes.

### `connectors/operator_mcp_adapter.py`

- **Inputs.** Reuse transport fixtures gathered in `tests/test_operator_transport_contract.py`, including Stage C trial entries and Stage E summaries.【F:tests/test_operator_transport_contract.py†L14-L175】
- **Execution.** Trigger REST↔gRPC parity tests and compare against the Neo transport pairing documented in the migration matrix.【F:docs/apsu_migration_matrix.md†L15-L15】
- **Expected logs.** Record handshake checksums, parity diffs, and fallback metadata. Highlight missing heartbeat telemetry as sandbox-only per the matrix notes.
- **Success criteria.** REST and gRPC payloads remain byte-for-byte identical, and checksum diffs flag only the deferred hardware telemetry gap.

## Success review checklist

1. All module logs stored under `logs/simulation_harness/` with timestamps and sandbox/hardware parity flags.
2. Migration matrix rows updated (if necessary) with new evidence paths after the harness run.【F:docs/apsu_migration_matrix.md†L5-L15】
3. Sandbox skips marked `environment-limited: <reason>` matching readiness packets.
4. Harness output attached to the readiness ledger entry that tracks the corresponding migration gate.

## Service runbooks

Each runbook below maps the simulation harness to the operator CLI, fixture repositories, and log validation snippets so reviewers can jump from doctrine to runnable examples. Cross-links point to the [APSU migration matrix](apsu_migration_matrix.md) rows that anchor each parity check and the sandbox contract suites that enforce transport evidence.【F:docs/apsu_migration_matrix.md†L5-L20】【F:tests/transport_parity/test_recorded_contracts.py†L1-L209】

### Memory service

- **CLI entry point.** `python scripts/bootstrap_memory.py --harness memory_store --fixtures tests/fixtures/memory/ --export logs/simulation_harness/memory_store/` replays the Codex harness snapshot for FAISS and SQLite shims before delegating to the Neo memory bundle.
- **Fixture paths.** Vector embeddings and FAISS shims live in `tests/fixtures/memory/`, while optional Stage C parity exports are catalogued beside the matrix row for [`memory_store.py`](apsu_migration_matrix.md#legacy-apsu-module-memory_storepy).【F:tests/test_memory_store.py†L12-L93】
- **Expected logs.** `memory_snapshot.json` should show identical `vector_ids`, `checksum`, and `environment-limited` fields for both Python and Neo-APSU executions. A passing run includes entries such as:

  ```json
  {"phase": "neo", "vector_ids": [101, 102], "checksum": "8f6c", "environment-limited": false}
  ```

  Any shimmed FAISS segments echo the environment limitation reason logged in Stage C readiness packets.

### Crown service

- **CLI entry point.** `python scripts/run_crown_harness.py --module crown_router --matrix docs/apsu_migration_matrix.md --log-root logs/simulation_harness/crown/` exercises `crown_router`, `crown_decider.py`, and servant routing in one pass, then shells out to the Neo PyO3 bindings referenced in the migration matrix.
- **Fixture paths.** Use dialog transcripts from `tests/fixtures/crown/transcripts/` and servant manifests from `tests/crown/fixtures/` to keep emotion scores, memory rows, and servant selection deterministic.【F:tests/crown/test_router_memory.py†L48-L91】【F:tests/crown/test_decider.py†L26-L74】
- **Expected logs.** Look for `expression_decision` and `servant_choice` records in `logs/simulation_harness/crown/harness.log`. A healthy run emits snippets like:

  ```json
  {"module": "crown_decider", "phase": "neo", "chosen_model": "moge.alpha", "affect_score": 0.82}
  ```

  Divergences trigger `environment-limited` markers and reference the migration matrix row for follow-up hardware validation.

### Identity service

- **CLI entry point.** `python scripts/run_crown_harness.py --module identity_loader --fixtures tests/fixtures/identity/ --log-root logs/simulation_harness/identity/` mirrors the Stage C identity rehearsal by bootstrapping persona, doctrine, and mission files before invoking `neoabzu_crown::load_identity`.
- **Fixture paths.** Mission/identity YAML lives under `tests/fixtures/identity/`, and parity-ready prompt bundles mirror `tests/apsu_migration/test_identity_loader_parity.py`.【F:tests/apsu_migration/test_identity_loader_parity.py†L35-L115】
- **Expected logs.** `identity_run.json` must contain `CROWN-IDENTITY-ACK`, matching fingerprint hashes, and GLM prompt sequences for both paths:

  ```json
  {"phase": "legacy", "fingerprint": "f9ad", "ack": "CROWN-IDENTITY-ACK"}
  ```

  Any missing acknowledgements signal a failed harness run and should be reflected in the readiness ledger.

### Transport service

- **CLI entry point.** `python scripts/run_transport_contracts.py --suite sandbox --log-root logs/simulation_harness/transport/` replays the REST↔gRPC contract suite referenced throughout the transport migration rows and beta rehearsal templates.【F:docs/releases/beta_rehearsal_template.md†L1-L120】
- **Fixture paths.** Recorded payloads reside in `tests/fixtures/transport_parity/`, and the orchestrator parity contracts are implemented in `tests/transport_parity/test_recorded_contracts.py`.【F:tests/transport_parity/test_recorded_contracts.py†L1-L209】
- **Expected logs.** `contract_suite.log` should log paired entries:

  ```json
  {"phase": "sandbox", "endpoint": "stage-c1-exit-checklist", "checksum_match": true}
  ```

  Failures surface `checksum_match: false` with diff paths so reviewers can jump to the recorded suites and replay them locally.

## Future hardware replay

Stage F soak alignment will replay this same harness with native binaries during the gate-runner hardware window. The Stage F plan calls for checksum-matched exports, MCP heartbeat captures, and sandbox skip retirements once the Neo binaries execute on hardware, so archive the Codex harness outputs now to streamline that replay.【F:docs/stage_f_plus_plan.md†L11-L33】

## Appendix: Gate-runner hardware replay workflow

Once Neo binaries are available, rerun the simulation harness on gate-runner hardware to retire `environment-limited` skips and align doctrine with the Stage G parity packets.

1. **Tooling.** Provision the gate-runner image with the same CLI entry points listed above plus hardware-only dependencies (`faiss-gpu`, DAW plug-ins, MCP credential bundles) recorded in the Stage F readiness plan.【F:docs/stage_f_plus_plan.md†L11-L33】【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L33】 Install `python scripts/run_transport_contracts.py --suite hardware` to capture GPU-backed transport diffs.
2. **Datasets.** Sync sandbox fixtures from `tests/fixtures/` and merge with hardware telemetry exports archived in `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/`. The migration matrix row for each service lists the exact readiness packet bundle to replay so auditors can trace lineage from Codex to hardware.【F:docs/apsu_migration_matrix.md†L5-L36】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】
3. **Approval workflow.** Submit the replay results through the Stage D/E bridge review captured in the readiness minutes, attach contract suite logs, and request sign-off from the gate captain, telemetry lead, and doctrine steward before merging updates to roadmap/status trackers.【F:docs/PROJECT_STATUS.md†L162-L205】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L39】 Hardware approvals must reference the updated doctrine entry and include checksum hashes for every contract suite artifact replayed.

