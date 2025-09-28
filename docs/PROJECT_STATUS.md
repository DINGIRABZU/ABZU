# Project Status

![Coverage](../coverage.svg)

The badge above is generated via `scripts/export_coverage.py`, which runs
`coverage-badge` after tests complete.

See [component_maturity.md](component_maturity.md) for per-component maturity metrics.

This document summarizes the current state of the ABZU codebase. It serves as a living roadmap covering repository layout, milestones, open issues, and release targets.

## Repository Structure

- **INANNA_AI/** – Core modules including adaptive learning, ethical validation, and audio analysis.
- **INANNA_AI_AGENT/** – Command line interface that activates the system and interacts with models.
- **audio/** – Audio processing utilities and backends for handling waveforms and feature extraction.
- **crown_config/** – Pydantic settings models and environment variable parsing.
- **connectors/** – Integrations with external services and APIs (see [Connector Index](connectors/CONNECTOR_INDEX.md)).
- **tests/** – Unit tests for learning modules, connectors, and audio helpers.
- **docs/** – Architecture overviews, deployment guides, and design notes.

## Test Run (pytest --maxfail=1 --cov -q)

```
pytest --maxfail=1 -q \
  --cov=start_spiral_os \
  --cov=spiral_os \
  --cov=spiral_memory \
  --cov=spiral_vector_db \
  --cov=vector_memory \
  --cov-fail-under=90 \
  tests/test_start_spiral_os.py \
  tests/test_spiral_os.py \
  tests/integration/test_razar_failover.py \
  tests/test_spiral_memory.py \
  tests/test_vector_memory.py \
  tests/test_vector_memory_extensions.py \
  tests/test_vector_memory_persistence.py \
  tests/test_spiral_vector_db.py \
  tests/crown/test_replay_determinism.py
```

Stage A rehearsals now exercise the Spiral OS boot entry points alongside Spiral memory and vector regression tests. Runs must meet the ≥90 % coverage bar for the module list specified in the command above, mirroring the scope visualized in `coverage.svg`; failures block promotion from the gate.

**Regression note (Stage A):** keep the optional memory stub instrumentation (`memory.optional.spiral_memory`, `memory.optional.vector_memory`) wired into the gate so the Alpha rehearsals continue reporting ≥90 % coverage even when the heavy backends are unavailable.

The replay regression writes `monitoring/crown_replay_summary.json` so contributors can confirm the scenario count, runtime, and divergence status without re-running the suite. The Alpha gate copies the summary into `logs/alpha_gate/<timestamp>/` alongside coverage exports.

## Recent Refactoring

- Standardized import order in `tools.session_logger`, `tools.sandbox_session`, and `tools.reflection_loop`.
- Added smoke tests covering reflection and session logging utilities.
- Reordered imports in `learning_mutator`, `state_transition_engine`, and `archetype_shift_engine` and added transformation smoke tests.

## Completed Milestones
- [Sovereign voice pipeline](https://github.com/DINGIRABZU/ABZU/pull/38) — owner: @DINGIRABZU.
- [Audio pipeline refresh](https://github.com/DINGIRABZU/ABZU/pull/194) — owner: @DINGIRABZU.

## Active Tasks
- [Milestone VIII – Sonic Core & Avatar Expression Harmonics](https://github.com/DINGIRABZU/ABZU/issues/208) — owner: @DINGIRABZU (see [milestone_viii_plan.md](milestone_viii_plan.md)).
- [Spiral OS stability](https://github.com/DINGIRABZU/ABZU/issues/210) — owner: ops team.
- [Pydantic v2 migration](https://github.com/DINGIRABZU/ABZU/issues/211) — owner: @DINGIRABZU.
- [FastAPI lifespan migration](https://github.com/DINGIRABZU/ABZU/issues/212) — owner: web team.
- [Optional dependency stubs](https://github.com/DINGIRABZU/ABZU/issues/213) — owner: infra team.
- **Sprint planning checklist:** Flag Stage A pipeline changes during sprint planning so operations can reserve the gate hardware or queue an alternative backlog slice. The Stage A1/A2/A3 failures in the [Stage A evidence register](#stagea-evidence-register)—missing `env_validation`, unavailable `crown_decider`, and aborted automation shakeouts—show how unplanned access stalls the sprint when this step is skipped.

## Planned Releases
- v0.1 – minimal Spiral OS boot sequence and CLI tools (target: Q3 2025). **Status:** Charter baseline approved in [alpha_v0_1_charter.md](alpha_v0_1_charter.md); subsystem execution tracked through the [Alpha v0.1 execution plan](roadmap.md#alpha-v01-execution-plan). Stage snapshots: **Stage A** focuses on Alpha gate automation readiness, **Stage B** locks subsystem hardening for sonic core, memory, and connectors, and **Stage C** synchronizes exit checklist, demo assets, and readiness signals. See the [Milestone Stages overview](roadmap.md#milestone-stages) for task-level detail. Reference the [Python Alpha Squad dossier](onboarding/python_alpha_squad.md) for RAZAR boot ownership and daily reliability rituals feeding that plan.
  - Stage C planners should review the optional dependency fallback matrix in [optional_dependency_fallbacks.md](optional_dependency_fallbacks.md) to align stakeholder communications whenever rehearsals operate with degraded subsystems.
- v0.2 – avatar console integration and basic RAG pipeline (target: Q4 2025). **Status:** Backlog shaping pending Alpha v0.1 exit criteria.

## Alpha v0.1 Readiness Gate
- Workflow defined in [docs/releases/alpha_v0_1_workflow.md](releases/alpha_v0_1_workflow.md) covering packaging, mandatory health checks, and acceptance tests.
- Automation available through `scripts/run_alpha_gate.sh` with optional connector sweeps and pytest argument passthrough. Each invocation writes evidence to `logs/alpha_gate/<timestamp>/` and refreshes the `logs/alpha_gate/latest` pointer.
- GitHub Actions [`Alpha Gate`](../.github/workflows/alpha_gate.yml) runs on pushes to `main`, a weekly Monday 06:00 UTC schedule, and on-demand dispatch to gate release candidates. The job restores cached `dist/` wheels, starts mock connector probes, and publishes the full `logs/alpha_gate/<timestamp>/` directory (plus the `latest` symlink) and build artifacts for review. Successful runs append a stamped entry to `CHANGELOG.md` inside the log bundle for audit trails, so operators must ensure each bundle is uploaded without overwriting prior evidence.
- Dry runs validate build artifact generation (`python -m build --wheel`) and Spiral OS / RAZAR acceptance coverage ahead of staging promotion. The same steps are codified in [`deployment/pipelines/alpha_gate.yml`](../deployment/pipelines/alpha_gate.yml) for local `spiral-os pipeline deploy` rehearsal.
- Doctrine drift is now gated by `python scripts/check_identity_sync.py`. If the check reports that `data/identity.json` predates updates to the mission, persona, Absolute Protocol, ABZU blueprint, or awakening overview doctrine, rerun `python scripts/refresh_crown_identity.py --use-stub` before continuing the gate.

> [!IMPORTANT]
> **Codex sandbox dependency limits.** Alpha rehearsals inside the Codex sandbox may lack GPUs, DAW backends, database drivers, or external credentials. Mark blocked steps with an `environment-limited` skip (mirroring the reason in test output), attach the command transcript to the relevant `logs/` bundle, and record the escalation in the operator risk queue before requesting hardware validation outside the sandbox. Follow the routing codified in [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment) and update change logs accordingly.

### Stage A evidence register

The 20250926 Stage A gate run (`logs/alpha_gate/20250926T115603Z/`) is the
canonical review artifact for the alpha readiness gate; reviewers should cross
check the accompanying Prometheus exports in
[`monitoring/alpha_gate.prom`](../monitoring/alpha_gate.prom) and
[`monitoring/alpha_gate_summary.json`](../monitoring/alpha_gate_summary.json) to
see the recorded metrics snapshot from that bundle.

| Timestamp (UTC) | Location | Notes |
| --- | --- | --- |
| 2025-09-27T23:54:25Z | `logs/alpha_gate/20250927T235425Z/command_log.md` | Sandbox run captured missing `python -m build`, absent `pytest-cov` hooks from `pytest.ini`, no recent self-heal cycles, and Stage B connector probes returning `503`, so coverage enforcement stays blocked pending hardware validation.【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】【F:logs/alpha_gate/20250927T235425Z/build_wheel.log†L1-L1】【F:logs/alpha_gate/20250927T235425Z/check_requirements.log†L1-L7】【F:logs/alpha_gate/20250927T235425Z/health_check_connectors.log†L1-L5】【F:logs/alpha_gate/20250927T235425Z/pytest_coverage.log†L1-L6】 |
| 2025-09-28T00:46:57Z | `logs/stage_a/latest/stage_a1_boot_telemetry-summary.json` | Stage A1 boot telemetry completed with sandbox overrides and captured the missing-credential and CPU fallback warnings in `stderr_tail` for audit.【F:logs/stage_a/20250928T004644Z-stage_a1_boot_telemetry/summary.json†L1-L31】 |
| 2025-09-28T00:47:22Z | `logs/stage_a/latest/stage_a2_crown_replays-summary.json` | Stage A2 replay capture ran all five scenarios while logging sandbox override notices for each deterministic comparison in the tail of the stderr transcript.【F:logs/stage_a/20250928T004714Z-stage_a2_crown_replays/summary.json†L1-L31】 |
| 2025-09-28T00:47:57Z | `logs/stage_a/latest/stage_a3_gate_shakeout-summary.json` | Stage A3 gate shakeout finished with success while the summary bundle retained the environment-limited warnings for every skipped phase to mirror the sandbox run book.【F:logs/stage_a/20250928T004738Z-stage_a3_gate_shakeout/summary.json†L1-L112】 |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout/summary.json` | Stage A3 gate shakeout recorded the automation transcript but still exited with status 1; investigate the follow-up triage noted in the summary before re-running. |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115245Z-stage_a2_crown_replays/summary.json` | Crown replay capture failed immediately because the `crown_decider` module is unavailable inside the container, leaving determinism checks blocked. |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry/summary.json` | Boot telemetry aborted during dependency validation; `env_validation` is missing so the bootstrap script cannot verify required environment variables. |
| 2025-09-23T20:05:07Z | `logs/stage_a/20250923T200435Z-stage_a3_gate_shakeout/summary.json` | Stage A3 gate shakeout packaged the wheel and passed requirements checks, but the self-healing verification step reported no successful cycles in the prior 24 h, so the run exited with status 1 and acceptance tests were skipped. |
| 2025-09-23T20:04:21Z | `logs/stage_a/20250923T200406Z-stage_a2_crown_replays/summary.json` | Stage A2 Crown replay capture again failed determinism: the `crown_glm_reflection` scenario hash diverged and the Neo4j driver remained unavailable, preventing task flow logging despite audio/video artifacts being captured. |
| 2025-09-23T20:03:37Z | `logs/stage_a/20250923T200333Z-stage_a1_boot_telemetry/summary.json` | Stage A1 boot telemetry stalled after reinstalling `faiss-cpu`; the bootstrap script aborted because HF_TOKEN, GITHUB_TOKEN, and OPENAI_API_KEY environment variables were missing in the container. |
| 2025-09-21T22:02:58Z | `logs/alpha_gate/20250921T220258Z/` | Coverage export failed in the container (missing `core.task_profiler` import during pytest collection), but build, health, and test phase logs were captured for the bundle review. |
| 2025-09-20T06:55:19Z | `logs/alpha_gate/20250920T065519Z/` | Successful gate run with 92.95 % coverage; bundle includes HTML coverage export, Prometheus counters, and phase logs for audit.【F:logs/alpha_gate/20250920T065519Z/coverage.json†L1-L1】 |

### Stage B evidence

- **Readiness ledger refresh (2025-09-28)** – [`readiness_index.json`](../logs/stage_b/latest/readiness_index.json) now tracks Stage B1 run `20250928T155301Z-stage_b1_memory_proof`, which rebuilt the cortex dataset, rehydrated the emotional telemetry, and completed with all eight layers ready, zero query failures, and p95/p99 latencies of 2.501 ms/3.579 ms. Stage B2 advanced to run `20250927T211008Z-stage_b2_sonic_rehearsal`, exporting a fresh `stage_b_rehearsal_packet.json`, while Stage B3 rotation `20250927T234018Z-stage_b3_connector_rotation` recorded the accepted `stage-b-rehearsal` and `stage-c-prep` contexts with the `20250928T001910Z-PT48H` window carrying credential expiry through 2025-09-30T00:19:10Z.【F:logs/stage_b/latest/readiness_index.json†L1-L33】【F:logs/stage_b/20250928T155301Z-stage_b1_memory_proof/summary.json†L1-L42】【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】【F:logs/stage_b/20250927T234018Z-stage_b3_connector_rotation/summary.json†L1-L83】
- **Load test (2025-09-20)** – [`load_test_summary.json`](../logs/stage_b/20250920T222728Z/load_test_summary.json) captures the 10 k document vector memory ingestion with p95 query latency at 19.95 ms and fallback store p95 at 93.92 ms, confirming the CPU rehearsal meets the <100 ms goal while preserving write throughput margins.【F:logs/stage_b/20250920T222728Z/load_test_summary.json†L1-L61】
- **Rehearsal bundle (2025-09-27)** – [`summary.json`](../logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json) logged the Stage B2 sonic rehearsal with a clean exit, every connector marked `doctrine_ok`, and the refreshed metrics explicitly capturing `dropouts_detected: 0` with no fallback warnings.【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】 The exported [`stage_b_rehearsal_packet.json`](../logs/stage_b_rehearsal_packet.json) mirrors those handshake and heartbeat payloads, each connector keeping an empty `doctrine_failures` list while rotating credentials for the `stage-b-rehearsal` context.【F:logs/stage_b_rehearsal_packet.json†L1-L144】 Published SHA-256 fingerprints: `summary.json` → `dce5368aa0cf2d5fe43b9238f8e4eb1b3b17ceb95ad05b4355dc3216ff9dc61d`, `stage_b_rehearsal_packet.json` → `2fbbced52eafdf46e6b90c9e77c92aec03fe96d5c43527037de5345e9ba18a90`.【4d71e5†L1-L3】【3eaaba†L1-L2】
- **Connector rotation acceptance (2025-09-26)** – [`summary.json`](../logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json) captures the Stage B3 drill with handshake and heartbeat payloads for `operator_api`, `operator_upload`, and `crown_handshake`, then archives the updated ledger beside the bundle. The rotation log now records the stub rehearsal window `20250926T180231Z-PT48H` and the acceptance window `20250926T180300Z-PT48H`, extending the earlier `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and the `20251024T174210Z-PT48H` refresh to keep every connector within the mandated 48-hour cadence.【F:logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json†L1-L55】【F:logs/stage_b_rotation_drills.jsonl†L24-L33】

### Stage C planning snapshot

- **Audio dependency remediation:** Rehearsal audio checks continue to report missing FFmpeg, simpleaudio, CLAP, and RAVE packages, locking media playback into fallback modes until the toolchain is provisioned.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L23-L40】
- **Health automation activation:** Stage B rehearsal health checks remain skipped, indicating the automated probes still need wiring before Stage C gate reviews.【F:logs/stage_b/20250921T122529Z/rehearsal_summary.json†L4-L15】
- **Memory and connector prerequisites:** The refreshed readiness ledger shows Stage B1 completing with all eight layers ready and zero query failures, while the Stage C readiness bundle records the accepted `stage-b-rehearsal` and `stage-c-prep` contexts plus the current `20250928T173339Z-PT48H` rotation window for the `operator_api` pilot. Keep the rotation cadence inside the 48-hour SLA as hardware access is scheduled.【F:logs/stage_b/latest/readiness_index.json†L1-L47】【F:logs/stage_b/20250928T155301Z-stage_b1_memory_proof/summary.json†L1-L42】【F:logs/stage_c/20250930T210000Z-readiness_packet/readiness_bundle/readiness_bundle.json†L175-L209】
- **Readiness packet assembly (2025-09-30T21:00:00Z):** `logs/stage_c/20250930T210000Z-readiness_packet/` now anchors the Stage C readiness bundle with live links into Stage A/B runs, the Stage C MCP parity drill, and the Stage C1 checklist that keeps python packaging and coverage marked as hardware-only follow-ups for the 2025-10-02 gate-runner-02 window.【F:logs/stage_c/20250930T210000Z-readiness_packet/readiness_bundle/readiness_bundle.json†L175-L227】【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】
- **Cross-team readiness review (2025-09-30T19:00Z):** Release Ops, Memory, Connector, QA, and Ops leads approved a _conditional GO_ for the beta kickoff contingent on the 2025-10-02 hardware replay. Action items cover the python `-m build` transcript, pytest coverage rerun, gRPC rollout brief, and roadmap metric annotations, each traced to owners and due dates so the beta bridge inherits a single source of truth.【F:logs/stage_c/20250930T210000Z-readiness_packet/review_minutes.md†L1-L33】【F:logs/stage_c/20250930T210000Z-readiness_packet/checklist_logs/stage_c1_exit_checklist_summary.json†L13-L33】
- **Hardware replay schedule:** The Stage C1 checklist summary pins the gate hardware rerun to `gate-runner-02` on 2025-10-02 18:00 UTC, aligning packaging and coverage retries with the Absolute Protocol sandbox bridge so deferred tasks close before beta ignition.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】
- **gRPC pilot commitments:** The MCP drill index and parity summary confirm REST↔gRPC equivalence for `operator_api`, capturing the accepted contexts and checksums that integration will replay once the hardware gap closes. The refreshed transport helpers now emit latency, error, and fallback metrics (`operator_api_transport_latency_ms`, `operator_api_transport_errors_total`, `operator_api_transport_fallback_total`) so the Grafana deck outlined in `monitoring/operator_transport_pilot.md` can compare REST and gRPC behaviour while the pilot stays confined to the annotated connectors. The accompanying contract tests validate that both transports return identical payloads and that gRPC falls back to REST without losing command parity, keeping readiness reviewers aligned on pilot scope before expansion.【F:logs/stage_c/20250930T210000Z-readiness_packet/mcp_drill/index.json†L1-L8】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】【F:tests/test_operator_transport_contract.py†L1-L78】
- **Stage C3 readiness sync (2025-09-28T20:28:34Z):** The refreshed bundle copies Stage A runs `20250928T004644Z-stage_a1_boot_telemetry`, `20250928T004714Z-stage_a2_crown_replays`, and `20250928T004738Z-stage_a3_gate_shakeout`, promotes the latest Stage B summaries (`20250928T155301Z-stage_b1_memory_proof`, `20250927T211008Z-stage_b2_sonic_rehearsal`, `20250927T234018Z-stage_b3_connector_rotation`), and now reports `requires_attention` solely because Stage A sandbox warnings persist—the Stage B snapshot carries no risk notes after the memory proof and rotation refresh. Readiness reviewers continue to mirror the sandbox gate sweep in `logs/alpha_gate/20250927T235425Z/` while hardware coverage remains deferred.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/summary.json†L1-L210】【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-summary.json†L1-L37】【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b2-summary.json†L1-L36】【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b3-summary.json†L1-L52】【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】
- **Stage C2 storyline freeze (2025-09-30T23:59:59Z):** Replayed the scripted demo harness against the refreshed Stage B media manifest so the Stage C bundle now copies the asset URIs and integrity fingerprints emitted by Stage B alongside the Stage C replay hashes.【3222c5†L1-L8】【1bb329†L1-L86】【2e72c1†L1-L37】
- **Stakeholder alert (2025-09-27T21:40:41Z):** Logged the Stage B memory stub and connector context risks to `logs/operator_escalations.jsonl` so downstream reviewers see the `requires_attention` escalation while remediation is scheduled.【F:logs/operator_escalations.jsonl†L1-L1】
- **Stage C4 operator MCP drill (2025-09-26T22:28:13Z):** The sandbox drill stored fresh `mcp_handshake.json` and `heartbeat.json` artifacts under the Stage C log while appending the `20250926T183842Z-PT48H` operator rotation window to the ledger. The heartbeat mirrors the Stage C drill event and keeps the credential expiry aligned with the readiness bundle review.【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/mcp_handshake.json†L1-L17】【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/heartbeat.json†L1-L9】【F:logs/stage_b_rotation_drills.jsonl†L30-L35】

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

