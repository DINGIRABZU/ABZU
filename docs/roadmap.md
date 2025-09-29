# Roadmap

_Last updated: 2025-10-31_

This roadmap tracks five core milestones on the path to a stable release. Each stage lists its expected outcome so contributors know when to advance to the next phase.

## Milestone Stages

| Stage | Expected Outcome | Status |
| --- | --- | --- |
| Vision Alignment | Shared project vision documented and initial requirements agreed upon. | Complete |
| Prototype | Minimal viable framework demonstrating end‑to‑end flow. | Complete |
| Alpha Release | Core features implemented and internal testing underway. | In Progress |
| Beta Release | External feedback incorporated with performance and security hardening. | Pending |
| General Availability | Stable release with complete documentation and long‑term support plan. | Pending |

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
| **C2. Demo storyline freeze** | @audio-lab | Finalize the demo script assets and rehearsal artifacts for stakeholder sign-off. | Confirm the Stage B rehearsal telemetry meets the drop-free requirement and align with modulation presets. | Stage C bundle now ingests the latest Stage B media manifest so asset URIs and integrity hashes ride alongside the replay evidence before the final recording review.【3222c5†L1-L8】【1bb329†L1-L86】 |
| **C3. Readiness signal sync** | @ops-team | Compile the Alpha readiness packet summarizing boot success rates, replay fidelity, and subsystem metrics. | Pull the latest telemetry from Stage A and Stage B tasks, update `PROJECT_STATUS.md` with outstanding risks, and embed the sandbox-to-hardware rehearsal bridge notes required by [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). | Cross-team readiness review completed on **2025-10-01 19:30 UTC** using `logs/stage_c/20251001T010101Z-readiness_packet/`; the packet binds Stage A/B logs, the Stage C MCP gRPC parity trial, and a hardware-scheduled Stage C1 checklist so beta bridge approvals and pilot commitments live in one artifact, while the refreshed Stage C3 sync at `logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/` confirms Stage B is clear of risk notes ahead of the bridge.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_c/20251001T010101Z-readiness_packet/checklist_logs/stage_c1_exit_checklist_summary.json†L1-L33】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_c/20250929T105500Z-stage_c3_readiness_sync/summary.json†L1-L210】 |
| **C4. Operator MCP drills** | @ops-team | Land `OperatorMCPAdapter` for `operator_api`/`operator_upload` and confirm Stage B parity with `crown_handshake`. | Run `scripts/stage_b_smoke.py` to log the 48-hour credential rotation drill for each connector and archive the results under `logs/stage_b_rotation_drills.jsonl`, highlighting the successive windows `20250926T180300Z-PT48H`, `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20251024T174210Z-PT48H`, and the baseline `20250922T101554Z-PT48H` during roadmap syncs. | Latest drill `20250926T222813Z` keeps Stage B rehearsal and Stage C prep contexts accepted, archives the heartbeat/handshake payloads beside the readiness packet, and feeds the gRPC migration planning noted for the beta bridge review. The follow-on stub rotation captured REST and gRPC trace parity for each connector in the ledger and produced checksum-matched Stage C diff artifacts ahead of the beta bridge review window `20250928T173339Z-PT48H`.【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/summary.json†L1-L132】【F:logs/stage_c/20250926T222813Z-stage_c4_operator_mcp_drill/mcp_handshake.json†L1-L17】【F:logs/stage_b_rotation_drills.jsonl†L54-L58】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】 |

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

### Stage E – Transport/beta readiness

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **E1. Transport parity enforcement** | @ops-team | Lock REST and gRPC parity for operator surfaces ahead of the beta external window. | Import Stage D bridge diffs into the transport pilot dashboards and stage contract tests beside the readiness ledger. | Execute the transport parity suite across connectors, archive checksum-matched traces, and gate beta kickoff on the resulting ledger status.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/test_operator_transport_contract.py†L1-L103】 |
| **E2. Beta rehearsal telemetry bundle** | @monitoring-guild | Publish a consolidated telemetry packet spanning Stage B rehearsals through Stage D bridges so beta stakeholders inherit the same metrics. | Align telemetry schemas with the Stage C readiness packet and Stage D bridge manifests; verify dashboards accept the combined payload. | Export the beta rehearsal bundle, stamp Grafana dashboards, and append checksum/timestamp metadata to the doctrine ledger for review.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】【F:logs/stage_c/20251003T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】 |
| **E3. External beta launch readiness** | @release-ops | Compile the go/no-go packet that merges production bridge sign-offs with beta transport parity commitments. | Draft the beta readiness outline referencing the Stage D ledger and transport enforcement plan while capturing outstanding environment-limited skips. | Present the beta readiness packet during weekly reviews, capture risk acknowledgements, and trigger the external beta announcement once signatures are archived.【F:logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json†L1-L41】【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】 |

Stage E extends the Stage C transport pilot: contract tests and dashboards now act as beta gatekeepers, and the weekly review agenda should add the Stage D bridge ledger alongside the existing parity drill recap.

## Maintenance

Update this roadmap and `CHANGELOG.md` whenever a milestone is completed to record progress and guide future planning. Documentary additions such as [banana_rater.md](banana_rater.md) should be cross-linked when new evaluation flows launch.
