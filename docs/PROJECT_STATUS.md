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
> **Codex sandbox dependency limits.** Alpha rehearsals inside the Codex sandbox may lack GPUs, DAW backends, database drivers, or external credentials. Follow the guardrails in [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints): mark blocked steps with an `environment-limited` skip (mirroring the reason in test output), attach the command transcript to the relevant `logs/` bundle, and record the escalation in the operator risk queue before requesting hardware validation outside the sandbox. Coordinate follow-ups with the sandbox-to-hardware bridge plan in [roadmap.md](roadmap.md#stage-g-sandbox-to-hardware-bridge-validation) so sprint reviews see when hardware remediation will execute, and update change logs accordingly.

### Stage A evidence register

The 20250926 Stage A gate run (`logs/alpha_gate/20250926T115603Z/`) is the
canonical review artifact for the alpha readiness gate; reviewers should cross
check the accompanying Prometheus exports in
[`monitoring/alpha_gate.prom`](../monitoring/alpha_gate.prom) and
[`monitoring/alpha_gate_summary.json`](../monitoring/alpha_gate_summary.json) to
see the recorded metrics snapshot from that bundle.

- **Archive every Stage A acceptance run.** After each Stage A promotion attempt,
  compress and store the entire `logs/alpha_gate/<timestamp>/` directory with the
  Prometheus exports and Crown replay summaries copied by the workflow helper so
  the evidence chain remains reproducible for follow-up reviews.【F:docs/releases/alpha_v0_1_workflow.md†L46-L119】

The 2025-11-05 sandbox sweep completed Stage A1/A2/A3 while logging
environment-limited warnings: bootstrap recorded missing python packaging,
docker, audio, and coverage tooling; Crown replays fell back to deterministic
FFmpeg/SoX stubs; and the Alpha gate shakeout marked build, health, and tests as
sandbox skips while still persisting the summary bundle.【F:logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json†L1-L36】【F:logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json†L1-L32】【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】

| Timestamp (UTC) | Location | Notes |
| --- | --- | --- |
| 2025-11-05T17:20:00Z | `logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json` | Alpha gate shakeout ran under `--sandbox`, marking build, health, and tests as environment-limited while recording missing python -m build, docker/SoX/FFmpeg/aria2c, requests, and coverage badge tooling without aborting.【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】 |
| 2025-11-05T17:10:00Z | `logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json` | Crown replay capture completed with deterministic hashes; FFmpeg/SoX gaps triggered environment-limited warnings while sandbox stubs handled media exports.【F:logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json†L1-L32】 |
| 2025-11-05T17:00:00Z | `logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json` | Bootstrap finished after logging missing python -m build, docker, SoX, FFmpeg, aria2c, and pytest-cov tooling as environment-limited warnings instead of aborting.【F:logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json†L1-L36】 |
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

- **Readiness ledger refresh (2025-12-05)** – [`readiness_index.json`](../logs/stage_b/latest/readiness_index.json) now tracks Stage B1 run `20251205T142355Z-stage_b1_memory_proof`, which documented the sandbox `neoabzu_memory` shim while keeping all eight layers ready with zero query failures and p95/p99 latencies of 2.287 ms/3.301 ms. Stage B2 remains anchored to `20250927T211008Z-stage_b2_sonic_rehearsal`, and Stage B3 rotation `20251205T160210Z-stage_b3_connector_rotation` captured the refreshed `20251205T160210Z-PT48H` window plus sandbox overrides for operator_api/operator_upload/crown_handshake so credential expiry stays in the ledger.【F:logs/stage_b/latest/readiness_index.json†L1-L33】【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L56】【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】【F:logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json†L1-L94】
- **Continuous ledger upkeep.** Refresh the memory load proofs, sonic rehearsal
  bundles, and connector rotation receipts between reviews so Stage C readers see
  the latest evidence without waiting for ad-hoc exports.【F:logs/stage_b/latest/readiness_index.json†L1-L47】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L119-L199】
- **Credential window snapshot (2025-10-03)** – The merged readiness packet copies the newest `operator_api` rotation ledger entry into `mcp_drill/rotation_metadata.json`, preserving the `credential_window` emitted by the Stage B smoke rehearsal so reviewers can confirm the `stage-b-rehearsal` and `stage-c-prep` contexts without scraping the JSONL ledger.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/rotation_metadata.json†L1-L80】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L119-L148】
- **Load test (2025-09-20)** – [`load_test_summary.json`](../logs/stage_b/20250920T222728Z/load_test_summary.json) captures the 10 k document vector memory ingestion with p95 query latency at 19.95 ms and fallback store p95 at 93.92 ms, confirming the CPU rehearsal meets the <100 ms goal while preserving write throughput margins.【F:logs/stage_b/20250920T222728Z/load_test_summary.json†L1-L61】
- **Rehearsal bundle (2025-09-27)** – [`summary.json`](../logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json) logged the Stage B2 sonic rehearsal with a clean exit, every connector marked `doctrine_ok`, and the refreshed metrics explicitly capturing `dropouts_detected: 0` with no fallback warnings.【F:logs/stage_b/20250927T211008Z-stage_b2_sonic_rehearsal/summary.json†L1-L74】 The exported [`stage_b_rehearsal_packet.json`](../logs/stage_b_rehearsal_packet.json) mirrors those handshake and heartbeat payloads, each connector keeping an empty `doctrine_failures` list while rotating credentials for the `stage-b-rehearsal` context.【F:logs/stage_b_rehearsal_packet.json†L1-L144】 Published SHA-256 fingerprints: `summary.json` → `dce5368aa0cf2d5fe43b9238f8e4eb1b3b17ceb95ad05b4355dc3216ff9dc61d`, `stage_b_rehearsal_packet.json` → `2fbbced52eafdf46e6b90c9e77c92aec03fe96d5c43527037de5345e9ba18a90`.【4d71e5†L1-L3】【3eaaba†L1-L2】
- **Connector rotation refresh (2025-12-05)** – [`summary.json`](../logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json) records the Stage B3 smoke run copying sandbox overrides, doctrine status, and the `20251205T160210Z-PT48H` ledger entries for the operator and Crown connectors. The rotation JSONL now includes the fresh window alongside the prior `20250926T180231Z-PT48H`, `20250926T180300Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and `20251024T174210Z-PT48H` receipts so auditors can see the 48-hour cadence maintained through the latest rehearsal.【F:logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json†L1-L94】【F:logs/stage_b_rotation_drills.jsonl†L70-L115】

### Stage C planning snapshot

- **Audio dependency remediation:** Rehearsal audio checks continue to report missing FFmpeg, simpleaudio, CLAP, and RAVE packages, locking media playback into fallback modes until the toolchain is provisioned.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L23-L40】
- **Health automation activation:** Stage B rehearsal health checks remain skipped, indicating the automated probes still need wiring before Stage C gate reviews.【F:logs/stage_b/20250921T122529Z/rehearsal_summary.json†L4-L15】
- **Resolve flagged gaps before Stage C.** Treat the missing audio dependencies
  and dormant health automation as blockers for Stage C sign-off; remediation
  status must be updated in the ledger alongside each refreshed rehearsal bundle
  so the exit review can verify the fixes landed.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L23-L40】【F:logs/stage_b/20250921T122529Z/rehearsal_summary.json†L4-L15】【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L199】
- **Memory and connector prerequisites:** The refreshed readiness ledger shows Stage B1 executing with the sandbox bundle (neoabzu shim) while keeping all eight layers ready and zero query failures, and Stage B3 now advertises the `20251205T160210Z-PT48H` credential window for the operator and Crown connectors. Carry that window into Stage C readiness so the bridge review can verify sandbox-to-hardware evidence without scraping raw logs.【F:logs/stage_b/latest/readiness_index.json†L1-L47】【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L56】【F:logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json†L1-L94】
- **Stage A sandbox sweep (2025-11-05):** Stage A1/A2/A3 now log environment-limited warnings for missing python packaging, docker/SoX/FFmpeg tooling, the requests client, and coverage badge generation while still emitting the summary bundle; hardware promotion remains pending until gate-runner-02 access is restored.【F:logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json†L1-L36】【F:logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json†L1-L32】【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】
- **Readiness packet assembly (2025-10-03T01:01:01Z):** `logs/stage_c/20251003T010101Z-readiness_packet/` now anchors the Stage C readiness bundle with live links into Stage A/B runs, the Stage C MCP parity drill, and the Stage C1 checklist while surfacing the new `credential_window` snapshot for the operator MCP pilot.【F:logs/stage_c/20251003T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】
- **Cross-team readiness review (2025-10-02T16:00Z):** Release Ops, Memory, Connector, QA, and Ops leads booked a beta-planning walkthrough for 2025-10-02 ahead of the gate-runner rehearsal to triage the Stage A tooling gaps called out in the merged readiness bundle, align on MCP credential windows, and confirm the evidence links they will surface in the bridge review.【F:logs/stage_c/20251001T091834Z-stage_c3_readiness_sync/readiness_bundle.json†L7-L110】【F:logs/stage_c/20251001T091834Z-stage_c3_readiness_sync/readiness_bundle.json†L437-L520】
- **Hardware replay schedule:** The Stage C1 checklist summary pins the gate hardware rerun to `gate-runner-02` on 2025-10-02 18:00 UTC, aligning packaging and coverage retries with the Absolute Protocol sandbox bridge so deferred tasks close before beta ignition.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】
- **gRPC pilot commitments:** The MCP drill index and parity summary confirm REST↔gRPC equivalence for `operator_api`, capturing the accepted contexts and checksums that integration will replay once the hardware gap closes. The refreshed transport helpers now emit latency, error, and fallback metrics (`operator_api_transport_latency_ms`, `operator_api_transport_errors_total`, `operator_api_transport_fallback_total`) so the Grafana deck outlined in `monitoring/operator_transport_pilot.md` can compare REST and gRPC behaviour while the pilot stays confined to the annotated connectors. The accompanying contract tests validate that both transports return identical payloads and that gRPC falls back to REST without losing command parity, keeping readiness reviewers aligned on pilot scope before expansion.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】【F:tests/test_operator_transport_contract.py†L1-L78】
- **gRPC pilot commitments:** The MCP drill index and parity summary confirm REST↔gRPC equivalence for `operator_api`, capturing the accepted contexts and checksums that integration will replay once the hardware gap closes. The refreshed transport helpers now emit latency, error, and fallback metrics (`operator_api_transport_latency_ms`, `operator_api_transport_errors_total`, `operator_api_transport_fallback_total`) so the Grafana deck outlined in `monitoring/operator_transport_pilot.md` can compare REST and gRPC behaviour while the pilot stays confined to the annotated connectors. The accompanying contract tests validate that both transports return identical payloads and that gRPC falls back to REST without losing command parity, keeping readiness reviewers aligned on pilot scope before expansion.【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L222】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】【F:tests/test_operator_transport_contract.py†L1-L78】

#### Stage C risk register

| Risk | Owner | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| Stage A sandbox toolchain gaps keep readiness in `requires_attention`. | @ops-team | Stage C3 bundle cannot clear the beta readiness gate until build, health, and coverage steps run with full tooling. | Provision the missing build/test utilities (python-build tooling, Docker, FFmpeg, aria2c) in the sandbox and rerun Stage A rehearsals before the beta review sync. | ⚠️ Watch list 【F:logs/stage_c/20251001T091834Z-stage_c3_readiness_sync/readiness_bundle.json†L7-L210】 |

#### Beta bridge readiness review agenda (2025-10-08 sync)

- **Present Stage C transport parity drill.** Walk leads through the REST and gRPC handshake artifacts plus the diff confirmation captured in the beta bridge summary so the pilot scope, accepted contexts, and checksum parity remain visible to the readiness panel.【F:docs/roadmap.md†L98-L107】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】
- **Action – close latency instrumentation gap.** The monitoring payload now emits `rest_latency_missing` and `grpc_latency_missing` alerts for the Stage C trial; connectors and ops must hook latency counters before the pilot graduates from the beta bridge window.【F:connectors/operator_mcp_adapter.py†L164-L265】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】
- **Action – restore Stage C heartbeat emission.** `heartbeat_emitted` remained `false` in the trial bundle, triggering the `heartbeat_missing` alert; readiness owners should either reinstate the heartbeat or document the fallback flow ahead of kickoff.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L42】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】
- **Action – expand parity enforcement checks.** Add the new transport parity checksum test to the readiness gate so both transports stay in lockstep as connectors roll onto the pilot.【F:tests/test_operator_transport_contract.py†L79-L103】【F:connectors/operator_mcp_adapter.py†L202-L265】
- **Follow-up – publish monitoring payload to Grafana.** Feed `build_transport_parity_monitoring_payload` into the operator transport board so alerts surface automatically during beta bridge drills.【F:connectors/operator_mcp_adapter.py†L267-L288】
- **Stage C3 readiness sync (2025-10-01T09:18:34Z):** The `/alpha/stage-c3-readiness-sync` run merged Stage A boot, replay, and shakeout summaries with the latest Stage B1/B2/B3 evidence. Stage A completes with environment-limited risk notes covering build tooling, health probes, and coverage dependencies, while Stage B reports green statuses with the sandbox MCP contexts and credential window aligned to the `20250926T222814Z-PT48H` rotation. Overall readiness remains `requires_attention` until the Stage A toolchain gaps close.【F:logs/stage_a/latest/stage_a1_boot_telemetry-summary.json†L1-L40】【F:logs/stage_a/latest/stage_a2_crown_replays-summary.json†L1-L48】【F:logs/stage_a/latest/stage_a3_gate_shakeout-summary.json†L1-L44】【F:logs/stage_c/20251001T091834Z-stage_c3_readiness_sync/readiness_bundle.json†L7-L210】【F:logs/stage_c/20251001T091834Z-stage_c3_readiness_sync/readiness_bundle.json†L437-L520】
- **Stage C2 storyline freeze (2025-09-30T23:59:59Z):** Replayed the scripted demo harness against the refreshed Stage B evidence manifest so the Stage C bundle now mirrors the published upload hints, SHA-256 fingerprints, and cue metadata instead of copying stems into git. The latest `/alpha/stage-c2-demo-storyline` run (`20251001T085114Z-stage_c2_demo_storyline`) documents the zero-drop replay, the updated `session_01_media.tar.gz` checksum (`7d7e5f8f…`), and the new Stage C archive manifest for auditors.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L78】【F:evidence_manifests/stage-b-audio.json†L1-L77】【F:evidence_manifests/stage-c-demo-storyline.json†L1-L40】
- **Stakeholder alert (2025-09-27T21:40:41Z):** Logged the Stage B memory stub and connector context risks to `logs/operator_escalations.jsonl` so downstream reviewers see the `requires_attention` escalation while remediation is scheduled.【F:logs/operator_escalations.jsonl†L1-L1】
- **Stage C4 operator MCP drill (2025-10-01T09:32:13Z):** The latest sandbox drill published refreshed `mcp_handshake.json`/`heartbeat.json` artifacts with the Stage B rehearsal and Stage C prep contexts tagged as accepted via the MCP adapter, then logged matching 48-hour rotation windows for the operator, upload, and Crown connectors in the Stage B ledger. The Stage B3 smoke receipt mirrors the updated credential expiry so the beta review can trace MCP parity from rehearsal through the promotion checklist.【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/summary.json†L1-L38】【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/mcp_handshake.json†L1-L33】【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/heartbeat.json†L1-L14】【F:logs/stage_b_rotation_drills.jsonl†L77-L79】【F:logs/stage_b/20251001T093529Z-stage_b3_connector_rotation/stage_b_smoke.json†L1-L33】

#### Stage C outcome recap (2025-10-01 – 2025-10-31)

- **Readiness bundle status.** `logs/stage_c/20251001T010101Z-readiness_packet/` remains the canonical Stage C packet, merging Stage A environment-limited notes, the Stage B rehearsal ledger, and the MCP parity drill into a single artifact. The bundle flags the blocked gate-runner hardware replay while tracking the successful Stage B1/B2/B3 evidence and the gRPC pilot diff that beta owners must inherit.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L2-L195】
- **Demo storyline freeze.** The Stage C2 scripted replay locked the stakeholder demo assets to the Stage B manifest, replaying the arrival/handoff/closing cues without dropouts and recording the refreshed `session_01_media.tar.gz` checksum in the readiness archives.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L123】
- **Operator MCP drill.** The Stage C4 sandbox drill validated REST↔gRPC parity for the operator pilot, logging matching checksums, credential rotation windows, and accepted contexts while surfacing missing heartbeat metrics that must be restored during hardware promotion.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】
- **Residual hardware follow-ups.** Hardware coverage and packaging still need to replay on `gate-runner-02`, and the parity drill must emit heartbeat telemetry before beta sign-off. The pending items remain tagged in the Stage C1 exit checklist, Stage C readiness bundle, and Stage B1 memory refresh summary that highlights sandbox overrides for emotional telemetry and crown services.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L2-L171】【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L20-L29】

> [!UPCOMING]
> **Next readiness review:** 2025-10-04 16:00 UTC (host: @release-ops) to present the Stage C recap and Stage D/E objectives. Minutes will be captured at `logs/stage_c/20251004T160000Z-readiness_review/minutes.md` and attached under `logs/stage_c/20251001T010101Z-readiness_packet/updates/` so downstream squads consume the roadmap adjustments without waiting for a separate rollout memo.

### Stage D bridge snapshot

| Objective | Owner | Entry Criteria | Exit Criteria | Hardware Replay Reference |
| --- | --- | --- | --- | --- |
| Replay the Stage C readiness bundle on production hardware. | @ops-team | Stage C1 exit checklist completed with hardware rerun scheduled on `gate-runner-02`; readiness bundle `20251001T010101Z` pinned with Stage A risk notes and MCP drill artifacts. | Gate-runner replay captures parity diffs, checklist attachments, and review minutes updates in the Stage D ledger for downstream audits. | Mirror `logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json` and `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` on hardware runners before promotion.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L2-L195】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】 |
| Promote Neo-APSU binaries with sandbox parity. | @neoabzu-core | Stage B rotation ledger and Stage C MCP drill establish checksum and rotation baselines for REST↔gRPC parity. | Hardware rollout publishes crate fingerprints, connector rotation receipts, and parity traces that match the sandbox bundle before widening access. | Replay the rotation windows recorded in `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` and Stage B rotation drills while capturing new hardware parity manifests.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L120-L195】【F:logs/stage_b_rotation_drills.jsonl†L12-L45】【F:operator_api_grpc.py†L1-L148】 |
| Extend transport telemetry dashboards to hardware spans. | @release-ops | Sandbox Grafana board and handshake diff demonstrate transport parity but highlight missing heartbeat metrics. | Production bridge emits latency/heartbeat telemetry alongside REST↔gRPC checksums, and the diff is archived with dashboard links for readiness reviews. | Re-run the Stage C parity drill on hardware and ingest results into `monitoring/operator_transport_pilot.md` plus the Stage D ledger.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】【F:monitoring/operator_transport_pilot.md†L1-L39】 |

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

| Objective | Owner | Entry Criteria | Exit Criteria | Hardware Replay Reference |
| --- | --- | --- | --- | --- |
| Lock REST↔gRPC parity as a beta gate. | @release-ops | Stage C parity drill and Stage E transport readiness snapshot confirm checksum matches while flagging missing latency metrics. | Weekly beta reviews include checksum-matched trace bundles and contract test results tied to Grafana dashboards with hardware spans. | Replay the Stage C handshake bundle during hardware rehearsals and attach updated traces to `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/` before beta sign-off.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】【F:tests/test_operator_transport_contract.py†L1-L320】 |
| Restore connector heartbeat telemetry. | @integration-guild | Stage C bundle and Stage E readiness report both show `heartbeat_emitted: false` and missing latency metrics for operator, upload, and Crown connectors. | Hardware replay exports heartbeat payloads and latency series for all connectors, updating the readiness packet and Grafana dashboards. | Capture heartbeat payloads during the gate-runner replay and publish them alongside the Stage E connector traces for downstream squads.【F:logs/stage_c/20251031T000000Z-test/summary.json†L7-L50】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L34-L115】【F:monitoring/operator_transport_pilot.md†L1-L84】 |
| Document beta governance & approvals. | @qa-alliance | Stage C readiness minutes capture conditional GO status pending hardware reruns; beta launch plan references transport governance requirements. | Beta readiness packet includes updated minutes, sign-offs, and governance checklist entries aligned with hardware parity evidence. | Append the 2025-10-04 readiness review minutes and subsequent approvals to the Stage C packet before circulating the beta launch governance brief.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】【F:docs/releases/beta_launch_plan.md†L47-L76】 |
- **External comms alignment:** Stage E’s go/no-go packet draws on the Stage D bridge ledger plus the transport handshake artifacts already logged in the Stage C trial so communication owners can cite identical evidence in stakeholder updates and reference the Neo-APSU governance checklist for connector sign-off.【F:logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json†L1-L41】【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】【F:docs/connectors/CONNECTOR_INDEX.md†L1-L86】

#### Stage E risk register

| Risk | Owner | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| Missing parity trace uploads for weekly reviews. | @ops-team | Beta gate cannot confirm transport stability. | Automate uploading Stage D/E trace bundles to the evidence ledger and cross-link in roadmap/PROJECT_STATUS updates. | 🛠️ In progress 【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】 |
| Stage E heartbeat latency instrumentation missing in sandbox snapshot. | @integration-guild | Beta rollout blocks until `operator_api`, `operator_upload`, and `crown_handshake` emit heartbeat metrics alongside the recorded parity traces. | Track the heartbeat panel on the continuous dashboard and refresh the readiness packet once latency signals land. | ⚠️ Watch list 【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L31-L63】【F:monitoring/operator_transport_pilot.md†L1-L84】 |
| Telemetry schemas diverge across rehearsal bundles. | @monitoring-guild | Grafana dashboards drop fields during beta rehearsals. | Validate schemas against readiness packet structure before exporting the beta rehearsal bundle. | ⚠️ Watch list 【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】 |
| Beta comms lack signed transport approvals. | @release-ops | External announcement slips without documented sign-off. | Capture signatures in the beta readiness packet and archive alongside Stage D bridge sign-offs. | 🔄 Pending approval 【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】 |

### Stage G

| Run | Operator Lead | Hardware/Service Owner | QA Reviewer | Approvals | Evidence |
| --- | --- | --- | --- | --- | --- |
| `20251102T090000Z-stage_g_gate_runner_hardware` | @ops-team (signed 2025-11-02T09:32:10Z) | @infrastructure-hardware (signed 2025-11-02T09:33:45Z) | @qa-alliance (signed 2025-11-02T09:34:20Z) | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml` | `summary.json`, `parity_diff.json`, and `rollback_drill.md` confirm the gate-runner replay matched the Stage C readiness bundle and exercised the rollback drill before hardware promotion.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/rollback_drill.md†L1-L24】 |
| `20251102T094500Z-stage_g_neo_apsu_parity` | @ops-team (signed 2025-11-02T09:59:41Z) | @neoabzu-core (signed 2025-11-02T10:00:17Z) | @qa-alliance (signed 2025-11-02T10:01:03Z) | `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml` | `summary.json`, `parity_diff.json`, and `transport_contract.json` show hardware parity against Stage B rotation windows plus the sandbox rollback transcript required by The Absolute Protocol.【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/transport_contract.json†L1-L20】【F:docs/The_Absolute_Protocol.md†L54-L114】 |

Stage G approvals demonstrate that sandbox-to-hardware bridge requirements have been satisfied with documented rollback drills, checksum parity diffs, and signed evidence bundles ahead of production bridge activities. Weekly status reviews should verify the approvals YAML files remain in sync with roadmap Stage G tasks and the doctrine checkpoint list in [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment).

### Beta launch checklist

Refer to the [Beta Launch Playbook](releases/beta_launch_plan.md) for guardrail
definitions and escalation instructions. Weekly reviews should confirm the
following items remain on track.【F:docs/releases/beta_launch_plan.md†L1-L111】

| Checklist Item | Owner | Evidence | Status | Notes |
| --- | --- | --- | --- | --- |
| Stage E transport parity bundle referenced in every beta decision | @ops-team | `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json` | ✅ Anchored | Checksum `30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8` verified against dashboards.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L87】 |
| Heartbeat latency remediation plan tracked | @integration-guild | Stage E summary + transport dashboard | ⚠️ Environment-limited | Latency metrics still absent in sandbox exporters; annotate dashboards until hardware rehearsal lands the signals.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L31-L63】【F:monitoring/operator_transport_pilot.md†L34-L66】 |
| External feedback exporter refreshed with latest run | @monitoring-guild | `logs/stage_f/exporters/latest.prom` | ✅ Captured | Histogram and gauges published for latency, error budgets, and satisfaction this week.【F:logs/stage_f/exporters/latest.prom†L1-L33】 |
| Security approvals mirrored in readiness minutes | @release-ops | Stage C readiness minutes + beta playbook | 🔄 Pending signatures | Awaiting updated credential attestations before widening beta access.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:docs/releases/beta_launch_plan.md†L47-L76】 |

### Beta risk tracker

| Risk | Owner | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| Beta feedback latency exceeds 250 ms p95 for any connector. | @ops-team | External testers experience sluggish workflows, eroding trust ahead of GA. | Investigate `beta_feedback_latency_regression` alerts, replay exporter snapshot, and align with transport parity traces before re-opening access. | 🛠️ In mitigation – monitoring alerts wired.【F:monitoring/alerts/beta_feedback.yml†L1-L20】【F:logs/stage_f/exporters/latest.prom†L1-L24】 |
| Error-budget ratio drops below 0.85 for consecutive reviews. | @monitoring-guild | Beta error budget burns down, forcing throttling or cohort reductions. | Pause new cohorts, ship fix, and document recovery steps in weekly review notes. | ⚠️ Watch – operator upload trending near threshold.【F:monitoring/alerts/beta_feedback.yml†L17-L28】【F:logs/stage_f/exporters/latest.prom†L25-L33】 |
| Satisfaction scores fall below CSAT 4.2 or NPS 40. | @release-ops | Stakeholder sentiment declines and blocks GA promotion. | Route `beta_feedback_satisfaction_drop` alerts through escalation notifier and capture remediation in feedback table. | 🔄 Monitoring – crown_handshake flagged for follow-up.【F:monitoring/alerts/beta_feedback.yml†L29-L43】【F:logs/stage_f/20251101T120000Z-beta_feedback/summary.json†L1-L34】 |

### Beta feedback tracking

| Channel | Telemetry Hash | p95 Latency (ms) | Error-Budget Ratio | CSAT | NPS | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `operator_api` | `30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8` | 215 | 0.91 | 4.35 | 47 | Sandbox testers reporting sluggish auth callbacks; hardware rehearsal scheduled.【F:logs/stage_f/20251101T120000Z-beta_feedback/summary.json†L1-L20】 |
| `operator_upload` | `30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8` | 232 | 0.88 | 4.21 | 42 | Upload retries tied to checksum validation; watching budget burn.【F:logs/stage_f/20251101T120000Z-beta_feedback/summary.json†L20-L27】 |
| `crown_handshake` | `30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8` | 241 | 0.86 | 4.18 | 39 | Avatar switching bug depressing satisfaction; fix slated for next rehearsal.【F:logs/stage_f/20251101T120000Z-beta_feedback/summary.json†L27-L34】 |

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

