# Roadmap

_Last updated: 2025-10-31_

This roadmap tracks five core milestones on the path to a stable release. Each stage lists its expected outcome so contributors know when to advance to the next phase.

## Charter & roadmap cadence

Bi-weekly working sessions align the charter backlog with the roadmap. Squad leads surface their next three Execution Ladder tasks, confirm interlocks, and record any required sign-offs so dependency owners can prepare before the following sprint checkpoint.【F:docs/alpha_v0_1_charter.md†L74-L88】 The resulting notes should update this roadmap and the companion status trackers so milestone reviews inherit the latest ownership and dependency signals.

## Milestone Stages

| Stage | Expected Outcome | Status |
| --- | --- | --- |
| Vision Alignment | Shared project vision documented and initial requirements agreed upon. | Complete |
| Prototype | Minimal viable framework demonstrating end‑to‑end flow. | Complete |
| Alpha Release | Core features implemented and internal testing underway. | Complete |
| Beta Release | External feedback incorporated with performance and security hardening. | Complete |
| General Availability | Stable release with complete documentation and long‑term support plan. | Complete |

## General Availability

The GA gate promoted on **2025-11-15** with evidence captured in
`logs/stage_h/20251115T090000Z-ga_hardware_cutover/`. The hardware telemetry
snapshot confirms parity with the Stage G bridge bundles and meets the LTS
thresholds in [`monitoring/README.md`](../monitoring/README.md#production-lts-thresholds).

- Review the GA readiness packet in [`docs/releases/ga_readiness.md`](releases/ga_readiness.md)
  for support SLAs, upgrade cadence, and deprecation policy details.
- Long-term support cadence and rollback governance live in
  [`docs/lts/ga_lts_plan.md`](lts/ga_lts_plan.md) with doctrine owner sign-off
  requirements.
- Incident response, rollback rehearsals, and telemetry exports must reference
  the GA summary bundle and approvals recorded alongside it.

## Alpha v0.1 Execution Plan

Alpha v0.1 focuses on delivering a reliable Spiral OS boot sequence paired with
predictable creative output. The table below enumerates the subsystems required
for the release, aligning owners, dependencies, and exit criteria. Use this plan
alongside [`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md), the
[Python Alpha Squad dossier](onboarding/python_alpha_squad.md), and the
[Alpha v0.1 charter](alpha_v0_1_charter.md) when coordinating weekly reviews.

| Subsystem | Objective | Owner | Dependencies | Exit Criteria |
| --- | --- | --- | --- | --- |
| Spiral OS Boot | Harden the boot pipeline and failover logic so the CLI can reliably initialize environments on first attempt. | @ops-team | Stable hardware profiles; finalized environment validation scripts. | Boot success rate ≥ 95% in three consecutive staging runs with telemetry published to `monitoring/boot_metrics.prom`. |
| Crown Orchestration | Deliver deterministic agent routing through Crown deciders with replayable session logs. | @crown-core | Spiral OS boot stability; updated session logger API. | Cross-agent flows replay without divergence across five recorded scenarios; regression suite green. |
| Memory Fabric | Optimize spiral memory ingestion and sharding for low-latency retrieval supporting alpha stories. | @memory-squad | Vector DB scaling checklist; connector mocks. | P95 retrieval latency ≤ 120 ms on 10k memory items; ingestion audit log complete. |
| Sonic Core & Avatar Expression | Stabilize audio synthesis and avatar expression harmonics for live demos. | @audio-lab | Crown orchestration metrics; updated modulation arrangement presets. | Demo script executes end-to-end with no audio dropouts in two live rehearsal sessions. |
| External Connectors | Refresh primary connector handshakes and authentication flows for alpha datasets. | @integration-guild | Approved API credential rotation plan. | Connector smoke tests green across three target services with 48-hour credential rotation rehearsal completed. |
| QA & Release Ops | Build release checklist, automated verification bundle, and rollback playbook. | @release-ops | All subsystem handoffs; new monitoring dashboards. | Checklist signed off by subsystem owners; dry-run release completed with rollback validation logs archived. |

### Stage A – Alpha gate confidence

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **A1. Spiral boot telemetry gate** | @ops-team | Align boot pipeline instrumentation with alpha gate metrics so first-attempt initialization hits the 95% success target. | Publish the stable hardware profile notes and confirm the environment validation scripts called out in the alpha charter are passing on the gate runner. | Run three consecutive staging boot rehearsals and archive telemetry snapshots for the Alpha gate audit bundle. |
| **A2. Crown replay verification** | @crown-core | Guarantee decider routing and session logs replay deterministically for gate reviews. | Sync the refreshed session logger API with Spiral OS boot stability milestones as documented in the charter interlocks. | Execute five cross-agent replay drills and deliver the resulting traces into the Alpha gate review packet. |
| **A3. Gate automation shakeout** | @release-ops | Harden `scripts/run_alpha_gate.sh` and the acceptance coverage described in the workflow guide before promoting builds. | Stage the build tooling, secrets, and health-check prerequisites from the workflow doc on the automation host. | Record a full dry-run Alpha gate run with packaging, health, and acceptance logs handed to Stage B owners. |

> [!NOTE]
> **Sprint planning checklist:** Flag Stage A pipeline changes during sprint planning so operations can schedule the gate hardware or supply alternate backlog. The Stage A1/A2/A3 failures logged in the [Stage A evidence register](PROJECT_STATUS.md#stagea-evidence-register)—missing `env_validation`, unavailable `crown_decider`, and aborted automation shakeouts—show how unplanned access halts progress when this step is skipped.

Operator consoles now expose Stage A automation directly through the `operator_api` endpoints:
`POST /alpha/stage-a1-boot-telemetry`, `POST /alpha/stage-a2-crown-replays`, and
`POST /alpha/stage-a3-gate-shakeout`. Each call archives stdout/stderr under
`logs/stage_a/<run_id>/` with a JSON summary so Stage B reviewers can consume gate evidence without
leaving the dashboard.

The Mission Map also collects the Stage B (`stage-b1-memory-proof`, `stage-b2-sonic-rehearsal`,
`stage-b3-connector-rotation`) and Stage C (`stage-c1-exit-checklist`, `stage-c2-demo-storyline`)
milestone controls under dedicated "Milestone Controls" groupings. Triggering any of these buttons
streams structured results into the event log and surfaces the artifact paths returned by the
corresponding `operator_api` handlers, keeping the roadmap audit trail anchored to
`logs/stage_[abc]/<run_id>/` evidence bundles.【F:web_console/game_dashboard/dashboard.js†L180-L356】【F:web_console/game_dashboard/mission_map.js†L1-L144】【F:operator_api.py†L2184-L2421】

> [!IMPORTANT]
> **Codex sandbox dependency limits.** When Stage A or Stage B rehearsals require GPUs, DAW plugins, or external connectors that the Codex sandbox cannot provide, mark affected tests as `environment-limited`, capture the skipped command output in the alpha bundle, and log the pending validation in change notes. Escalate hardware-required follow-ups through the operator risk queue in [PROJECT_STATUS.md](PROJECT_STATUS.md#stage-c-planning-snapshot) and align messaging with [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment).

> [!NOTE]
> **Sandbox audit (2025-09-27).** The latest Stage A sweep in `logs/alpha_gate/20250927T235425Z/` recorded missing build tooling, connector probes returning `503`, and `pytest.ini` coverage hooks failing without `pytest-cov`, so coverage gating remains deferred to the reserved hardware rehearsal window.【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】【F:logs/alpha_gate/20250927T235425Z/health_check_connectors.log†L1-L5】【F:logs/alpha_gate/20250927T235425Z/pytest_coverage.log†L1-L6】

### Stage B – Subsystem hardening

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **B1. Memory fabric load proof** | @memory-squad | Optimize spiral memory ingestion and sharding so alpha stories meet the ≤120 ms P95 retrieval target. | Provision the host with the Rust toolchain and Python development headers, compile the Neo-ABZU bundle via `cargo build -p neoabzu-memory --release`, and complete the vector DB scaling checklist alongside the charter’s connector mocks. | Capture ingestion audit logs, publish the 10k-item latency measurements, and investigate the native bundle’s core-layer failure reported in the latest run (995 query failures with `stubbed_bundle: false`).【F:NEOABZU/memory/README.md†L7-L13】【F:logs/stage_b/20250927T231955Z-stage_b1_memory_proof/summary.json†L1-L33】 |
| **B2. Sonic core rehearsal lock** | @audio-lab | Stabilize audio synthesis and avatar harmonics so the demo script runs end-to-end without dropouts. | Pair the updated modulation presets with Crown orchestration metrics, mirroring the Stage A outputs. | Conduct two live rehearsal sessions and archive telemetry showing zero audio dropouts. |
| **B3. Connector credential rotation** | @integration-guild | Refresh primary connector handshakes and authentication flows for alpha datasets. | Finalize the API credential rotation plan and prepare rehearsal stubs noted in the charter. | Run smoke tests across the three target services and document the 48-hour rotation drill results. |

#### Future Stage – gRPC adoption milestone

| Scope | Trigger | Exit Criteria |
| --- | --- | --- |
| Broaden gRPC interfaces across operator, memory, and connector pathways using the NeoABZU vector service contract as the canonical service pattern. | Promote from Stage B once connector drills and memory rehearsals log stable Stage gate evidence bundles, enabling the gRPC rollout to inherit verified telemetry flows. | Stage gate evidence ledger includes gRPC request/response traces, NeoABZU vector service parity checks, and operator rehearsal sign-off showing mixed REST/gRPC fallbacks without regression. |

The cross-team readiness review on **2025-10-01 19:30 UTC** reaffirmed the _conditional GO_: beta kickoff proceeds once the 2025-10-02 hardware replay completes, and the `operator_api` gRPC pilot advances using the parity traces captured in the refreshed readiness packet.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】

The pilot now instruments both transports with shared latency, error, and fallback
metrics plus span events, unlocking a dedicated Grafana board that compares the
REST baseline to the gRPC trial while logging fallback metadata for the Stage C
ledger.【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】【F:monitoring/operator_transport_pilot.md†L1-L39】 The
contract tests cover parity and fallback behaviour, keeping the roadmap
commitments tied to executable checks as adoption expands.【F:tests/test_operator_transport_contract.py†L1-L78】

### Stage C – Alpha exit prep

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **C1. Exit checklist consolidation** | @release-ops | Deliver the release checklist, verification bundle, and rollback playbook required for the alpha exit gate. | Aggregate subsystem handoffs and monitoring dashboards so the checklist draft mirrors Stage A/B deliverables. | Execute the dry-run release and archive rollback validation logs for the go/no-go review. |
| **C2. Demo storyline freeze** | @audio-lab | Finalize the demo script assets and rehearsal artifacts for stakeholder sign-off. | Confirm the Stage B rehearsal telemetry meets the drop-free requirement and align with modulation presets. | Stage C bundle now ingests the refreshed Stage B evidence manifest—`20251001T085114Z-stage_c2_demo_storyline` captures the zero-drop replay, references the packaged upload hints, and records the updated `session_01_media.tar.gz` checksum for doctrine reviewers.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L78】【F:evidence_manifests/stage-b-audio.json†L1-L77】 |
| **C3. Readiness signal sync** | @ops-team | Compile the Alpha readiness packet summarizing boot success rates, replay fidelity, and subsystem metrics. | Pull the latest telemetry from Stage A and Stage B tasks, update `PROJECT_STATUS.md` with outstanding risks, and embed the sandbox-to-hardware rehearsal bridge notes required by [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). | Cross-team readiness review completed on **2025-10-01 19:30 UTC** using `logs/stage_c/20251001T010101Z-readiness_packet/`; the packet binds Stage A/B logs, the Stage C MCP gRPC parity trial, and a hardware-scheduled Stage C1 checklist so beta bridge approvals and pilot commitments live in one artifact, while the refreshed Stage C3 sync at `logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/` confirms Stage B is clear of risk notes ahead of the bridge.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_c/20251001T010101Z-readiness_packet/checklist_logs/stage_c1_exit_checklist_summary.json†L1-L33】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/summary.json†L1-L210】 |
| **C4. Operator MCP drills** | @ops-team | Land `OperatorMCPAdapter` for `operator_api`/`operator_upload` and confirm Stage B parity with `crown_handshake`. | Run `scripts/stage_b_smoke.py` to log the 48-hour credential rotation drill for each connector and archive the results under `logs/stage_b_rotation_drills.jsonl`, highlighting the successive windows `20250926T180300Z-PT48H`, `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20251024T174210Z-PT48H`, and the refreshed `20251001T093213Z-PT48H` ledger entries during roadmap syncs. | Latest drill `20251001T093206Z` refreshed the Stage C handshake and heartbeat artifacts with the `stage-b-rehearsal`/`stage-c-prep` contexts accepted via the MCP adapter, recorded matching 48-hour windows for operator, upload, and Crown connectors, and aligned the Stage B3 smoke receipt’s credential expiry with the beta readiness ledger.【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/summary.json†L1-L38】【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/mcp_handshake.json†L1-L33】【F:logs/stage_b_rotation_drills.jsonl†L77-L79】【F:logs/stage_b/20251001T093529Z-stage_b3_connector_rotation/stage_b_smoke.json†L1-L33】 |

#### Beta bridge transport parity drill

- `logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json` captures the REST handshake accepted contexts, rotation window, and checksum for the operator beta bridge, matching the Stage C readiness targets.【F:logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json†L1-L41】
- The gRPC trial handshake mirrors the same session metadata and parity checksum under `logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json`, confirming transport equivalence ahead of pilot rollout.【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】
- `logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json` shows no payload differences and reports matching checksums, locking the beta bridge handshake scope before connector expansion.【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L11】
- The Stage C summary exposes the handshake artifact bundle while flagging `heartbeat_emitted: false`; the new connector monitoring payload now surfaces missing REST/gRPC latency and heartbeat alerts so the beta pilot can close instrumentation gaps prior to widening access.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】

Stage C planners should review the Sonic Core optional component inventory and
the rehearsal evidence packet before go/no-go reviews so degraded audio or
avatar fidelity is flagged early for demo stakeholders.【F:docs/sonic_core_harmonics.md†L23-L51】【F:logs/stage_b_rehearsal_packet.json†L217-L344】

### Stage D – Production bridge

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **D1. Hardware parity audit** | @ops-team | Confirm gate-runner and production racks emit matching telemetry, paving the bridge from Stage C rehearsal evidence into the hardware window. | Schedule hardware parity windows against the `gate-runner-02` slot logged for the Stage C1 checklist and mirror the readiness packet bundle on the production host. | Replay the Stage C readiness packet on the production runners, archive parity diffs under `logs/stage_d/<run_id>/`, and sign off the bridge ledger before Neo-APSU activation.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】 |
| **D2. Neo-APSU rollout rehearsal** | @neoabzu-core | Promote the Neo-APSU control plane and workspace crates into the bridge environment with parity against the Stage B rehearsal bundles. | Align crate fingerprints and PyO3 bindings against the readiness ledger and Stage B rotation manifests before copying binaries. | Deploy the Neo-APSU release candidates, execute connector rotations with REST↔gRPC parity captures, and publish the rollout manifest with checksum matches to the doctrine ledger.【F:logs/stage_b_rotation_drills.jsonl†L24-L58】【F:operator_api.py†L54-L374】【F:operator_api_grpc.py†L1-L148】 |
| **D3. Production telemetry handshake** | @release-ops | Extend the transport parity drill into the production bridge so dashboards reflect hardware metrics alongside sandbox trails. | Wire the Grafana transport board to accept Stage C payloads and Stage B rehearsal telemetry so alerts survive the environment swap. | Run the production bridge handshake, emit latency/error/fallback metrics to the shared dashboards, and document the parity diff for weekly risk reviews.【F:monitoring/operator_transport_pilot.md†L1-L39】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】 |

> [!TIP]
> Stage D inherits the sandbox-to-hardware bridge instructions from [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). Rehearsal bundles should mirror the Stage C ledger structure so downstream auditors replay parity results without bespoke tooling.

Recent sandbox remediation captured an explicit before/after of the Stage B1 memory proof in `logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/`. The baseline run remained stubbed (`environment_mode="sandbox"`) with the optional bundle, while the post-rebuild metrics show the native `neoabzu_memory` crate exporting hardware-grade readiness figures (`environment_mode="hardware"`) alongside sandbox override flags for the remaining shims.【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/before/summary.json†L1-L32】【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L1-L38】 Stage D reviewers should pull these snapshots into the bridge ledger so parity packets inherit the hardware/native distinction.

The emotional telemetry path is still fronted by sandbox shims, as shown by the persisted `emotional_state` override in the refreshed summary; clearing that flag requires replaying the load proof on the gate-runner hardware before Stage D can certify aura logging for the bridge.【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L20-L29】

### Stage E – Transport/beta readiness

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **E1. Transport parity enforcement** | @ops-team | Lock REST and gRPC parity for operator surfaces ahead of the beta external window with a continuous parity dashboard. | Import Stage D bridge diffs into the transport pilot dashboards, stage contract tests beside the readiness ledger, and publish the live Grafana board that compares REST↔gRPC latency, error, fallback, and heartbeat streams. | Execute the transport parity suite across connectors, archive checksum-matched traces, and refuse beta kickoff until the dashboard shows green parity and heartbeat signals for every Stage E connector.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L87】【F:monitoring/operator_transport_pilot.md†L1-L66】【F:tests/test_operator_transport_contract.py†L1-L320】 |
| **E2. Beta rehearsal telemetry bundle** | @monitoring-guild | Publish a consolidated telemetry packet spanning Stage B rehearsals through Stage D bridges so beta stakeholders inherit the same metrics, including heartbeat latency deltas. | Align telemetry schemas with the Stage C readiness packet and Stage D bridge manifests; verify dashboards accept the combined payload and log missing heartbeat latency in the risk register until the metric lands. | Export the beta rehearsal bundle, stamp Grafana dashboards, and append checksum/timestamp metadata to the doctrine ledger for review alongside explicit callouts for any metrics still missing from the Stage E dashboards.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L87】【F:tests/test_operator_transport_contract.py†L1-L320】 |
| **E3. External beta launch readiness** | @release-ops | Compile the go/no-go packet that merges production bridge sign-offs with beta transport parity commitments governed by Neo-APSU. | Draft the beta readiness outline referencing the Stage D ledger, transport enforcement plan, and Neo-APSU connector governance so external approvals track the same REST↔gRPC parity and heartbeat bars enforced in testing. | Present the beta readiness packet during weekly reviews, capture risk acknowledgements, record Neo-APSU governance sign-off for each connector rollout, and trigger the external beta announcement once signatures are archived.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/operator_api/rest_trace.json†L1-L55】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/operator_api/grpc_trace.json†L1-L72】【F:docs/connectors/CONNECTOR_INDEX.md†L1-L86】 |

Stage E extends the Stage C transport pilot: contract tests and dashboards now act as beta gatekeepers, and the weekly review agenda should add the Stage D bridge ledger alongside the existing parity drill recap. The Stage E snapshot at `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json` confirms checksum-matched parity traces for `operator_api`, `operator_upload`, and `crown_handshake` while flagging the sandbox heartbeat gaps and recording the shared telemetry hash (`30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8`) for dashboard verification.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L20-L87】【F:tests/test_operator_transport_contract.py†L231-L320】 Continuous reviews should keep the dashboard URL (`https://grafana.ops.abzu.dev/d/operator-transport-parity/continuous-stage-e`) in the readiness minutes until heartbeat latency lands in the sandbox feed.【F:monitoring/operator_transport_pilot.md†L1-L84】

> [!NOTE]
> **Transport governance handshake.** Roadmap updates now embed the REST↔gRPC contract suite status, Grafana parity dashboard hash, and MCP rotation ledger excerpts next to each Stage E checkpoint so PROJECT_STATUS inherits live telemetry expectations without waiting for separate rollups. Document beta gating decisions by citing the latest Stage B rotation windows, Stage C readiness bundle, and Stage E parity traces in both artifacts to prove sandbox evidence is being consumed by hardware replays when Neo-APSU services advance.【F:logs/stage_b_rotation_drills.jsonl†L1-L40】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L87】

#### Stage D–H Neo-APSU adoption matrix

| Legacy APSU component | Neo-APSU surface | Stage D hardware bridge | Stage E telemetry & contract gating | Stage F soak checkpoints | Stage G parity replay | Stage H production adoption |
| --- | --- | --- | --- | --- | --- | --- |
| `crown_decider.py` | `neoabzu_crown::route_decision` | Replay Stage B rotation windows and Stage C readiness hashes on gate-runner hardware before declaring the Rust decider ready, capturing parity diffs in the bridge ledger.【F:logs/stage_b_rotation_drills.jsonl†L1-L40】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L47】 | Publish contract test results and Grafana parity status beside roadmap/PROJECT_STATUS updates so beta owners monitor continuous telemetry feed health.【F:tests/test_operator_transport_contract.py†L1-L210】【F:monitoring/operator_transport_pilot.md†L1-L66】【F:docs/PROJECT_STATUS.md†L162-L181】 | Track soak-week telemetry using the Stage E dashboard hash while calling out sandbox heartbeat deferrals until hardware metrics land.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L48】 | Include Rust decider parity diffs in Stage G hardware bundles with rollback transcripts and approvals.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】 | Confirm GA cutover inherits the Stage G ledger hash and parity lineage when promoting the Rust decider into production.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L1-L28】 |
| `crown_prompt_orchestrator.py` | `neoabzu_rag::MoGEOrchestrator` | Stage D rehearsals mirror Stage B connector windows and Stage C transport diffs to validate retrieval on hardware runners before enabling Neo-APSU orchestrations.【F:logs/stage_b_rotation_drills.jsonl†L1-L40】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L11】 | Roadmap status entries point to REST↔gRPC dashboards and MCP parity artifacts so beta reviewers see orchestrator telemetry gaps immediately.【F:tests/test_operator_transport_contract.py†L211-L320】【F:monitoring/operator_transport_pilot.md†L40-L84】 | Soak-week notes retain sandbox trace links and dashboard hashes to show how Neo-APSU consumes Stage C parity evidence before expansion.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L20-L87】 | Stage G Neo-APSU parity logs archive orchestrator checksum diffs with rollback drills and approvals, proving sandbox evidence replayed on hardware.【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】 | GA readiness summary records the orchestrator telemetry hash carried from Stage G hardware bundles.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L1-L28】 |
| `servant_model_manager.py` | `neoabzu_crown` servant bridge | Hardware bridge rehearsals reuse Stage C readiness servant logs so Neo-APSU registry activation inherits sandbox evidence before rollout.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L48-L120】 | Contract dashboards surface servant telemetry parity and flag sandbox deferrals inside roadmap/PROJECT_STATUS checkpoints.【F:tests/test_operator_transport_contract.py†L1-L210】【F:monitoring/operator_transport_pilot.md†L1-L66】【F:docs/PROJECT_STATUS.md†L162-L181】 | Soak runs keep sandbox registry traces attached to dashboards until hardware counters align, documenting every deferred metric.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L49-L87】 | Stage G parity bundles capture servant rollback rehearsals with sandbox transcript references.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】 | GA ledger confirms servant telemetry matches Stage G approvals before closing the doctrine hash trail.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L1-L28】 |
| `state_transition_engine.py` | `neoabzu_crown::route_inevitability` | Stage D diff packets import Stage C inevitability traces so hardware rehearsals verify chakra transitions against sandbox evidence.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L121-L185】 | Roadmap and PROJECT_STATUS notes cite inevitability spans from contract runs so beta gating sees heartbeat gaps while telemetry stabilizes.【F:tests/test_operator_transport_contract.py†L1-L210】【F:monitoring/operator_transport_pilot.md†L1-L84】【F:docs/PROJECT_STATUS.md†L162-L181】 | Soak reviews tie sandbox inevitability logs to dashboard hashes until hardware parity clears lingering deferrals.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L49-L87】 | Stage G Neo-APSU parity records inevitability diffs with rollback instructions referencing sandbox origins.【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】 | GA hardware summary documents inevitability telemetry hash continuity from Stage G.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L1-L28】 |
| `memory_store.py` | `neoabzu_memory::MemoryBundle` | Stage D bridge aligns Stage B rotations with Stage C readiness latency metrics before switching hardware writes to the Rust bundle.【F:logs/stage_b_rotation_drills.jsonl†L1-L40】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】 | Telemetry updates publish memory checksum parity results through Grafana so roadmap/PROJECT_STATUS audiences monitor ingestion gaps during beta prep.【F:tests/test_operator_transport_contract.py†L231-L320】【F:monitoring/operator_transport_pilot.md†L1-L84】【F:docs/PROJECT_STATUS.md†L162-L181】 | Soak cycles document sandbox latency evidence alongside dashboard hashes until hardware metrics converge.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L20-L87】 | Stage G hardware bundle records memory checksum parity and sandbox replay transcripts under Neo-APSU approvals.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】 | GA cutover retains the memory parity hash from Stage G to prove production readiness.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L15-L28】 |
| `emotional_state.py` | `neoabzu_crown` expression pipeline | Stage D hardware checks replay Stage B rotation history with Stage C sandbox diffs to validate aura persistence under the Neo-APSU expression path.【F:logs/stage_b_rotation_drills.jsonl†L1-L40】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】 | Beta-facing updates surface expression heartbeat telemetry inside contract dashboards so deferrals stay visible while sandbox evidence feeds hardware replays.【F:tests/test_operator_transport_contract.py†L1-L210】【F:monitoring/operator_transport_pilot.md†L1-L66】【F:docs/PROJECT_STATUS.md†L162-L181】 | Soak tracking references sandbox aura transcripts plus dashboard hashes until Neo-APSU hardware emits continuous heartbeats.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L49-L87】 | Stage G parity approvals append aura diffs that cite sandbox evidence and rollback rehearsals.【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】 | GA summary confirms aura telemetry hash continuity from Stage G hardware bundles.【F:logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json†L1-L28】 |

### Stage G – Sandbox-to-hardware bridge validation

| Task | Owner | Hardware Validation Owner | Rollback Drill | Evidence Bundling |
| --- | --- | --- | --- | --- |
| **G1. Gate-runner parity replay** | @ops-team | @infrastructure-hardware | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/rollback_drill.md` rehearses the sandbox-first rollback that disables `gate_runner_enabled` and drains sessions via `operator_api` before resuming hardware once parity recovers. | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/parity_diff.json` binds the Stage C readiness bundle hash to the hardware replay with approvals in `approvals.yaml`. |
| **G2. Neo-APSU services parity** | @neoabzu-core | @neoabzu-core | `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/rollback_drill.md` walks the control-plane/workspace rollback using `scripts/stage_b_smoke.py` against the Stage B rotation ledger before re-enabling hardware. | `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/parity_diff.json` and `transport_contract.json` capture checksum matches, fallback events, and heartbeat recovery with signatures in `approvals.yaml`. |
| **G3. Evidence bundle stitching** | @qa-alliance | @ops-team | Rollback confirmation references the operator console export and sandbox replay noted in the Stage A/C readiness bundles to ensure gate-runner and Neo-APSU drills fall back to sandbox telemetry without data loss. | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json` and `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json` enumerate bundle hashes aligned with [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment). |

Stage G maps the sandbox-to-hardware bridge directives from The Absolute Protocol directly into the roadmap. Hardware rehearsals must cite the Stage C readiness minutes and bundle hashes, attach rollback transcripts, and archive approvals from the operator lead, hardware owner, and QA reviewer before promoting later bridges.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml†L1-L12】【F:docs/The_Absolute_Protocol.md†L54-L114】 Weekly reviews should confirm the `parity_diff.json` artifacts stay in sync with `logs/stage_c/20251001T010101Z-readiness_packet/` references and that rollback drills remain current before opening the production bridge window.

## Maintenance

Update this roadmap and `CHANGELOG.md` whenever a milestone is completed to record progress and guide future planning. Documentary additions such as [banana_rater.md](banana_rater.md) should be cross-linked when new evaluation flows launch. GA upkeep is governed by the LTS cadence in [`docs/lts/ga_lts_plan.md`](lts/ga_lts_plan.md), and quarterly reviews must refresh the doctrine hashes listed in [`docs/doctrine_index.md`](doctrine_index.md).
