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

The 2025-10-02 gate-runner-02 window remains unresolved—the sandbox refresh recorded
blocked hardware attempts for Stage A1/A2/A3 because python packaging, docker,
audio tooling, and coverage extensions are still unavailable, and the readiness
bundle continues to flag the same environment-limited risks until hardware access
is restored.【F:logs/stage_a/20251002T180000Z-stage_a1_boot_telemetry/summary.json†L1-L24】【F:logs/stage_a/20251002T181000Z-stage_a2_crown_replays/summary.json†L1-L23】【F:logs/stage_a/20251002T182000Z-stage_a3_gate_shakeout/summary.json†L1-L23】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L74】

| Timestamp (UTC) | Location | Notes |
| --- | --- | --- |
| 2025-10-02T18:20:00Z | `logs/stage_a/20251002T182000Z-stage_a3_gate_shakeout/summary.json` | Hardware shakeout stayed blocked because python packaging, docker, pytest-cov, and media tooling are still missing in the sandbox, so the gate-runner replay remains pending.【F:logs/stage_a/20251002T182000Z-stage_a3_gate_shakeout/summary.json†L1-L23】 |
| 2025-10-02T18:10:00Z | `logs/stage_a/20251002T181000Z-stage_a2_crown_replays/summary.json` | Crown replay capture could not attach to gate-runner-02—the sandbox lacks docker privileges plus SoX/FFmpeg/aria2c binaries needed for the hardware stream.【F:logs/stage_a/20251002T181000Z-stage_a2_crown_replays/summary.json†L1-L23】 |
| 2025-10-02T18:00:00Z | `logs/stage_a/20251002T180000Z-stage_a1_boot_telemetry/summary.json` | Stage A1 hardware bootstrap was skipped because the sandbox still cannot provision python -m build, docker, SoX, FFmpeg, aria2c, or pytest-cov, and it has no route to gate-runner-02.【F:logs/stage_a/20251002T180000Z-stage_a1_boot_telemetry/summary.json†L1-L24】 |
| 2025-09-27T23:54:25Z | `logs/alpha_gate/20250927T235425Z/command_log.md` | Sandbox run captured missing `python -m build`, absent `pytest-cov` hooks from `pytest.ini`, no recent self-heal cycles, and Stage B connector probes returning `503`, so coverage enforcement stays blocked pending hardware validation.【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】【F:logs/alpha_gate/20250927T235425Z/build_wheel.log†L1-L1】【F:logs/alpha_gate/20250927T235425Z/check_requirements.log†L1-L7】【F:logs/alpha_gate/20250927T235425Z/health_check_connectors.log†L1-L5】【F:logs/alpha_gate/20250927T235425Z/pytest_coverage.log†L1-L6】 |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout/summary.json` | Stage A3 gate shakeout recorded the automation transcript but still exited with status 1; investigate the follow-up triage noted in the summary before re-running. |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115245Z-stage_a2_crown_replays/summary.json` | Crown replay capture failed immediately because the `crown_decider` module is unavailable inside the container, leaving determinism checks blocked. |
| 2025-09-24T11:52:45Z | `logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry/summary.json` | Boot telemetry aborted during dependency validation; `env_validation` is missing so the bootstrap script cannot verify required environment variables. |
| 2025-09-23T20:05:07Z | `logs/stage_a/20250923T200435Z-stage_a3_gate_shakeout/summary.json` | Stage A3 gate shakeout packaged the wheel and passed requirements checks, but the self-healing verification step reported no successful cycles in the prior 24 h, so the run exited with status 1 and acceptance tests were skipped. |
| 2025-09-23T20:04:21Z | `logs/stage_a/20250923T200406Z-stage_a2_crown_replays/summary.json` | Stage A2 Crown replay capture again failed determinism: the `crown_glm_reflection` scenario hash diverged and the Neo4j driver remained unavailable, preventing task flow logging despite audio/video artifacts being captured. |
| 2025-09-23T20:03:37Z | `logs/stage_a/20250923T200333Z-stage_a1_boot_telemetry/summary.json` | Stage A1 boot telemetry stalled after reinstalling `faiss-cpu`; the bootstrap script aborted because HF_TOKEN, GITHUB_TOKEN, and OPENAI_API_KEY environment variables were missing in the container. |
| 2025-09-21T22:02:58Z | `logs/alpha_gate/20250921T220258Z/` | Coverage export failed in the container (missing `core.task_profiler` import during pytest collection), but build, health, and test phase logs were captured for the bundle review. |
| 2025-09-20T06:55:19Z | `logs/alpha_gate/20250920T065519Z/` | Successful gate run with 92.95 % coverage; bundle includes HTML coverage export, Prometheus counters, and phase logs for audit.【F:logs/alpha_gate/20250920T065519Z/coverage.json†L1-L1】 |

### Stage B evidence

- **Readiness ledger refresh (2025-09-29)** – [`readiness_index.json`](../logs/stage_b/latest/readiness_index.json) now tracks Stage B1 run `20250928T155301Z-stage_b1_memory_proof`, which rebuilt the cortex dataset, rehydrated the emotional telemetry, and completed with all eight layers ready, zero query failures, and p95/p99 latencies of 2.501 ms/3.579 ms. Stage B2 advanced to run `20250927T211008Z-stage_b2_sonic_rehearsal`, exporting a fresh `stage_b_rehearsal_packet.json`, while Stage B3 rotation `20250929T105142Z-stage_b3_connector_rotation` mirrored the Stage C drill by logging the accepted `stage-b-rehearsal` and `stage-c-prep` contexts with the `20250926T222814Z-PT48H` window that keeps credentials valid through 2025-09-28T22:28:14Z.【F:logs/stage_b/latest/readiness_index.json†L1-L33】【F:logs/stage_b/20250928T155301Z-stage_b1_memory_proof/summary.json†L1-L42】【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】【F:logs/stage_b/20250929T105142Z-stage_b3_connector_rotation/summary.json†L1-L74】
- **Credential window snapshot (2025-10-03)** – The merged readiness packet copies the newest `operator_api` rotation ledger entry into `mcp_drill/rotation_metadata.json`, preserving the `credential_window` emitted by the Stage B smoke rehearsal so reviewers can confirm the `stage-b-rehearsal` and `stage-c-prep` contexts without scraping the JSONL ledger.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/rotation_metadata.json†L1-L80】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L119-L148】
- **Load test (2025-09-20)** – [`load_test_summary.json`](../logs/stage_b/20250920T222728Z/load_test_summary.json) captures the 10 k document vector memory ingestion with p95 query latency at 19.95 ms and fallback store p95 at 93.92 ms, confirming the CPU rehearsal meets the <100 ms goal while preserving write throughput margins.【F:logs/stage_b/20250920T222728Z/load_test_summary.json†L1-L61】
- **Rehearsal bundle (2025-09-27)** – [`summary.json`](../logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json) logged the Stage B2 sonic rehearsal with a clean exit, every connector marked `doctrine_ok`, and the refreshed metrics explicitly capturing `dropouts_detected: 0` with no fallback warnings.【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】 The exported [`stage_b_rehearsal_packet.json`](../logs/stage_b_rehearsal_packet.json) mirrors those handshake and heartbeat payloads, each connector keeping an empty `doctrine_failures` list while rotating credentials for the `stage-b-rehearsal` context.【F:logs/stage_b_rehearsal_packet.json†L1-L144】 Published SHA-256 fingerprints: `summary.json` → `dce5368aa0cf2d5fe43b9238f8e4eb1b3b17ceb95ad05b4355dc3216ff9dc61d`, `stage_b_rehearsal_packet.json` → `2fbbced52eafdf46e6b90c9e77c92aec03fe96d5c43527037de5345e9ba18a90`.【4d71e5†L1-L3】【3eaaba†L1-L2】
- **Connector rotation acceptance (2025-09-26)** – [`summary.json`](../logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json) captures the Stage B3 drill with handshake and heartbeat payloads for `operator_api`, `operator_upload`, and `crown_handshake`, then archives the updated ledger beside the bundle. The rotation log now records the stub rehearsal window `20250926T180231Z-PT48H` and the acceptance window `20250926T180300Z-PT48H`, extending the earlier `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and the `20251024T174210Z-PT48H` refresh to keep every connector within the mandated 48-hour cadence.【F:logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json†L1-L55】【F:logs/stage_b_rotation_drills.jsonl†L24-L33】

### Stage C planning snapshot

- **Audio dependency remediation:** Rehearsal audio checks continue to report missing FFmpeg, simpleaudio, CLAP, and RAVE packages, locking media playback into fallback modes until the toolchain is provisioned.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L23-L40】
- **Health automation activation:** Stage B rehearsal health checks remain skipped, indicating the automated probes still need wiring before Stage C gate reviews.【F:logs/stage_b/20250921T122529Z/rehearsal_summary.json†L4-L15】
- **Memory and connector prerequisites:** The refreshed readiness ledger shows Stage B1 completing with all eight layers ready and zero query failures, while the Stage C readiness bundle copies the accepted `stage-b-rehearsal` and `stage-c-prep` contexts alongside the current `20250926T222814Z-PT48H` rotation window for the `operator_api` pilot. Keep the rotation cadence inside the 48-hour SLA as hardware access is scheduled.【F:logs/stage_b/latest/readiness_index.json†L1-L47】【F:logs/stage_b/20250928T155301Z-stage_b1_memory_proof/summary.json†L1-L42】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/readiness_bundle.json†L463-L548】
- **Stage A hardware follow-up (2025-10-02):** The readiness bundle refreshed at 01:01Z still lists Stage A risk notes as environment-limited and records the hardware rerun entry as blocked with an attempted_at timestamp, pending gate-runner-02 access and toolchain provisioning.【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L74】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L133-L199】
- **Readiness packet assembly (2025-10-03T01:01:01Z):** `logs/stage_c/20251003T010101Z-readiness_packet/` now anchors the Stage C readiness bundle with live links into Stage A/B runs, the Stage C MCP parity drill, and the Stage C1 checklist while surfacing the new `credential_window` snapshot for the operator MCP pilot.【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】
- **Cross-team readiness review (2025-10-03T18:00Z):** Release Ops, Memory, Connector, QA, and Ops leads scheduled the beta-planning walkthrough for 2025-10-05, documented the merged ledger link, and confirmed the credential window evidence needed for the bridge review.【F:logs/stage_c/20251003T010101Z-readiness_packet/review_minutes.md†L1-L48】【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】
- **Hardware replay schedule:** The Stage C1 checklist summary pins the gate hardware rerun to `gate-runner-02` on 2025-10-02 18:00 UTC, aligning packaging and coverage retries with the Absolute Protocol sandbox bridge so deferred tasks close before beta ignition.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】
- **gRPC pilot commitments:** The MCP drill index and parity summary confirm REST↔gRPC equivalence for `operator_api`, capturing the accepted contexts and checksums that integration will replay once the hardware gap closes. The refreshed transport helpers now emit latency, error, and fallback metrics (`operator_api_transport_latency_ms`, `operator_api_transport_errors_total`, `operator_api_transport_fallback_total`) so the Grafana deck outlined in `monitoring/operator_transport_pilot.md` can compare REST and gRPC behaviour while the pilot stays confined to the annotated connectors. The accompanying contract tests validate that both transports return identical payloads and that gRPC falls back to REST without losing command parity, keeping readiness reviewers aligned on pilot scope before expansion.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】【F:tests/test_operator_transport_contract.py†L1-L78】
- **gRPC pilot commitments:** The MCP drill index and parity summary confirm REST↔gRPC equivalence for `operator_api`, capturing the accepted contexts and checksums that integration will replay once the hardware gap closes. The refreshed transport helpers now emit latency, error, and fallback metrics (`operator_api_transport_latency_ms`, `operator_api_transport_errors_total`, `operator_api_transport_fallback_total`) so the Grafana deck outlined in `monitoring/operator_transport_pilot.md` can compare REST and gRPC behaviour while the pilot stays confined to the annotated connectors. The accompanying contract tests validate that both transports return identical payloads and that gRPC falls back to REST without losing command parity, keeping readiness reviewers aligned on pilot scope before expansion.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】【F:tests/test_operator_transport_contract.py†L1-L78】

#### Beta bridge readiness review agenda (2025-10-08 sync)

- **Present Stage C transport parity drill.** Walk leads through the REST and gRPC handshake artifacts plus the diff confirmation captured in the beta bridge summary so the pilot scope, accepted contexts, and checksum parity remain visible to the readiness panel.【F:docs/roadmap.md†L98-L107】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】
- **Action – close latency instrumentation gap.** The monitoring payload now emits `rest_latency_missing` and `grpc_latency_missing` alerts for the Stage C trial; connectors and ops must hook latency counters before the pilot graduates from the beta bridge window.【F:connectors/operator_mcp_adapter.py†L164-L265】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】
- **Action – restore Stage C heartbeat emission.** `heartbeat_emitted` remained `false` in the trial bundle, triggering the `heartbeat_missing` alert; readiness owners should either reinstate the heartbeat or document the fallback flow ahead of kickoff.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L42】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】
- **Action – expand parity enforcement checks.** Add the new transport parity checksum test to the readiness gate so both transports stay in lockstep as connectors roll onto the pilot.【F:tests/test_operator_transport_contract.py†L79-L103】【F:connectors/operator_mcp_adapter.py†L202-L265】
- **Follow-up – publish monitoring payload to Grafana.** Feed `build_transport_parity_monitoring_payload` into the operator transport board so alerts surface automatically during beta bridge drills.【F:connectors/operator_mcp_adapter.py†L267-L288】
- **Stage C3 readiness sync (2025-09-29T10:55:00Z):** The refreshed bundle copies Stage A runs `20250928T004644Z-stage_a1_boot_telemetry`, `20250928T004714Z-stage_a2_crown_replays`, and `20250928T004738Z-stage_a3_gate_shakeout`, promotes the latest Stage B summaries (`20250928T155301Z-stage_b1_memory_proof`, `20250927T211008Z-stage_b2_sonic_rehearsal`, `20250929T105142Z-stage_b3_connector_rotation`), and reports `requires_attention` solely because Stage A sandbox warnings persist—the Stage B snapshot now mirrors the Stage C drill without any pending context notes. Readiness reviewers continue to mirror the sandbox gate sweep in `logs/alpha_gate/20250927T235425Z/` while hardware coverage remains deferred.【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/summary.json†L1-L210】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/stage_b-b1-summary.json†L1-L37】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/stage_b-b2-summary.json†L1-L36】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/stage_b-b3-summary.json†L1-L74】【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】
- **Stage C2 storyline freeze (2025-09-30T23:59:59Z):** Replayed the scripted demo harness against the refreshed Stage B media manifest so the Stage C bundle now copies the asset URIs and integrity fingerprints emitted by Stage B alongside the Stage C replay hashes.【3222c5†L1-L8】【1bb329†L1-L86】【2e72c1†L1-L37】
- **Stakeholder alert (2025-09-27T21:40:41Z):** Logged the Stage B memory stub and connector context risks to `logs/operator_escalations.jsonl` so downstream reviewers see the `requires_attention` escalation while remediation is scheduled.【F:logs/operator_escalations.jsonl†L1-L1】
- **Stage C4 operator MCP drill (2025-09-26T22:28:13Z):** The sandbox drill stored fresh `mcp_handshake.json` and `heartbeat.json` artifacts under the Stage C log while appending the `20250926T183842Z-PT48H` operator rotation window to the ledger. The heartbeat mirrors the Stage C drill event and keeps the credential expiry aligned with the readiness bundle review.【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/mcp_handshake.json†L1-L17】【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/heartbeat.json†L1-L9】【F:logs/stage_b_rotation_drills.jsonl†L30-L35】

### Stage D bridge snapshot

- **Hardware parity rehearsal:** Stage C1 locked the production bridge on `gate-runner-02`, so Stage D hardware parity must replay the same readiness bundle while mirroring checklist evidence on the production racks.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】
- **Neo-APSU rollout prep:** The Stage B rotation ledger still lists mixed REST/gRPC traces, providing the checksum baseline that Stage D Neo-APSU deployments must match before widening hardware access.【F:logs/stage_b_rotation_drills.jsonl†L24-L58】【F:operator_api_grpc.py†L1-L148】
- **Transport dashboard wiring:** The transport pilot dashboards already compare REST and gRPC parity; Stage D needs the production bridge handshake diff attached so hardware metrics appear alongside sandbox telemetry.【F:monitoring/operator_transport_pilot.md†L1-L39】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】

#### Stage D Neo-APSU migration backlog

- **crown_decider.py → `neoabzu_crown::route_decision`.** Stage C readiness replays still inject the simplified sandbox stub, so Stage D must wire the Rust decision engine, MoGE orchestrator hooks, and validator gating while documenting the migration per the Rust doctrine workflow.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-artifact1.stderr.log†L3-L15】【F:NEOABZU/crown/src/lib.rs†L86-L210】【F:docs/documentation_protocol.md†L5-L28】
- **crown_prompt_orchestrator.py → `neoabzu_rag::MoGEOrchestrator`.** The async pipeline remained stubbed during Stage C evidence capture; Stage D should route replay traffic through the Rust orchestrator so retrieval/ranking telemetry lands in the readiness ledger.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-artifact1.stderr.log†L7-L15】【F:NEOABZU/rag/src/lib.rs†L122-L177】
- **state_transition_engine.py → `neoabzu_crown::route_inevitability`.** Deterministic rotation stubs left ritual gating untested; Stage D must emit inevitability journeys from the Rust bridge and record the transition evidence in the doctrine bundle.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-artifact1.stderr.log†L5-L15】【F:NEOABZU/crown/src/lib.rs†L200-L210】
- **servant_model_manager.py → `neoabzu_crown` servant bridge.** Sandbox runs hid servant telemetry behind the local-registry stub; migrate to the Rust-managed registry so Stage D rehearsals capture invocation metrics and validator callbacks.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-artifact1.stderr.log†L11-L15】【F:NEOABZU/crown/src/lib.rs†L102-L189】
- **memory_store.py → `neoabzu_memory::MemoryBundle`.** Stage C readiness reported `cortex layer empty`, forcing optional memory stubs; Stage D must close the gap by porting persistence and verification to the Rust bundle so all eight layers report ready.【F:logs/stage_c/20250927T201020Z-stage_c3_readiness_sync/summary.json†L590-L627】【F:NEOABZU/memory/src/lib.rs†L12-L120】
- **emotional_state.py → `neoabzu_crown` expression pipeline.** The in-memory sandbox shim suppressed persisted aura updates; Stage D must align emotional telemetry with the Rust expression options and doctrine logging expectations.【F:logs/stage_c/20250928T202834Z-stage_c3_readiness_sync/stage_b-b1-artifact1.stderr.log†L9-L15】【F:NEOABZU/crown/src/lib.rs†L60-L197】

#### Stage D risk register

| Risk | Owner | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| Hardware slot slip on gate-runner-02 delays parity replay. | @ops-team | Hardware rehearsal blocks Neo-APSU launch and Stage E countdown. | Reserve backup window and mirror the Stage C1 checklist artifacts in the production bridge ledger for rapid reschedule. | 🔄 Pending scheduling 【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】 |
| Neo-APSU crate drift from rehearsal checksums. | @neoabzu-core | Divergent binaries invalidate transport parity traces. | Compare SHA-256 fingerprints against the Stage B rotation ledger before copying crates into hardware. | ⚠️ Watch list 【F:logs/stage_b_rotation_drills.jsonl†L24-L58】 |
| Transport metrics omit hardware spans after bridge cutover. | @release-ops | Beta readiness packet lacks production telemetry. | Attach the Stage D handshake diff to Grafana dashboards and verify parity metrics stream alongside sandbox history. | 🛠️ In progress 【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】 |
| Emotional telemetry still routes through sandbox shims. | @ops-team | Aura logging remains uncertified for Stage D until gate-runner sensors feed the native pipeline. | Reserve gate-runner execution to replay the memory load proof with hardware instrumentation and refresh the readiness packet. | ⚠️ Watch list 【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L20-L29】 |

### Stage E beta readiness snapshot

- **Parity enforcement gates:** Contract tests for REST↔gRPC parity already guard the transport pilot; Stage E promotes them to beta entry criteria, ties results to the continuous dashboard, and requires checksum-matched trace bundles during weekly reviews.【F:tests/test_operator_transport_contract.py†L1-L210】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】
- **Connector rollout tracking:** Stage E onboarding targets `operator_api`, `operator_upload`, and `crown_handshake`; the latest parity evidence only covers `operator_api`, so weekly reviews must flag the missing connectors until their REST↔gRPC runs and heartbeat telemetry land in the ledger.【F:docs/connectors/CONNECTOR_INDEX.md†L1-L86】【F:tests/test_operator_transport_contract.py†L1-L210】
- **Telemetry ledger merge:** The readiness packet and MCP drill index catalog the contexts and credential windows that Stage E must merge into a beta rehearsal bundle for stakeholder dashboards while backfilling heartbeat latency metrics now called out as gaps.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/test_operator_transport_contract.py†L1-L210】
- **External comms alignment:** Stage E’s go/no-go packet draws on the Stage D bridge ledger plus the transport handshake artifacts already logged in the Stage C trial so communication owners can cite identical evidence in stakeholder updates and reference the Neo-APSU governance checklist for connector sign-off.【F:logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json†L1-L41】【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】【F:docs/connectors/CONNECTOR_INDEX.md†L1-L86】

#### Stage E risk register

| Risk | Owner | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| Missing parity trace uploads for weekly reviews. | @ops-team | Beta gate cannot confirm transport stability. | Automate uploading Stage D/E trace bundles to the evidence ledger and cross-link in roadmap/PROJECT_STATUS updates. | 🛠️ In progress 【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】 |
| Stage E connectors missing parity evidence. | @integration-guild | Beta rollout blocks until `operator_upload` and `crown_handshake` publish gRPC trials. | Track connector coverage in the parity dashboard and promote the next drill once heartbeat telemetry is live. | ⚠️ Watch list 【F:tests/test_operator_transport_contract.py†L1-L210】 |
| Telemetry schemas diverge across rehearsal bundles. | @monitoring-guild | Grafana dashboards drop fields during beta rehearsals. | Validate schemas against readiness packet structure before exporting the beta rehearsal bundle. | ⚠️ Watch list 【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】 |
| Beta comms lack signed transport approvals. | @release-ops | External announcement slips without documented sign-off. | Capture signatures in the beta readiness packet and archive alongside Stage D bridge sign-offs. | 🔄 Pending approval 【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】 |

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

