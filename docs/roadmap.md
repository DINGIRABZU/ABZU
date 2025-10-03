# Roadmap

_Last updated: 2025-11-16_

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

## Codex sandbox constraints

Roadmap updates must delineate what happened inside the Codex sandbox versus what still needs hardware so
weekly reviews avoid chasing impossible tests:

- **Sandbox-only tasks.** GPU renders, DAW-assisted rehearsals, FFmpeg exports, and Neo-APSU parity drills
  remain dry runs until the Stage D/E bridge backlog or the Stage G hardware window replays them on
  gate-runner hosts. Flag these items directly in the stage tables so owners inherit the constraint.
- **Environment-limited tagging.** Use the exact `environment-limited: <reason>` phrasing from test skips
  in each stage summary and link to the supporting bundle under `logs/<gate>/<timestamp>/`. Roadmap callouts
  should reference [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints) so reviewers
  can cross-check the policy.
- **Hardware replay linkage.** Whenever a roadmap item defers evidence, cite the follow-up slot in
  [PROJECT_STATUS.md](PROJECT_STATUS.md#stage-d-bridge-snapshot) or the Stage G bridge plan so migration work
  has a visible path from sandbox evidence to hardware approval.

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

| Task | Owner | Objective | Step 0 Look-ahead | Next up | Sandbox guidance | Hardware replay ID |
| --- | --- | --- | --- | --- | --- | --- |
| **A1. Spiral boot telemetry gate** | @ops-team | Align boot pipeline instrumentation with alpha gate metrics so first-attempt initialization hits the 95% success target. | Publish the stable hardware profile notes and confirm the environment validation scripts called out in the alpha charter are passing on the gate runner. | Replay the 2025-11-05 sandbox sweep (`environment-limited: python -m build unavailable`, missing docker/SoX/FFmpeg/aria2c/`pytest-cov`) on hardware during the 2025-12-12 gate-runner slot and archive the refreshed telemetry bundle. 【F:logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json†L1-L36】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L13-L27】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry` |
| **A2. Crown replay verification** | @crown-core | Guarantee decider routing and session logs replay deterministically for gate reviews. | Sync the refreshed session logger API with Spiral OS boot stability milestones as documented in the charter interlocks. | Reproduce the 2025-11-05 sandbox replay hashes on hardware once FFmpeg/SoX are restored, clearing the `environment-limited` warnings logged in the latest Stage A2 bundle and attaching the updated evidence to the readiness packet. 【F:logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json†L1-L32】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L13-L30】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_a/20251105T171000Z-stage_a2_crown_replays` |
| **A3. Gate automation shakeout** | @release-ops | Harden `scripts/run_alpha_gate.sh` and the acceptance coverage described in the workflow guide before promoting builds. | Stage the build tooling, secrets, and health-check prerequisites from the workflow doc on the automation host. | Convert the 2025-11-05 sandbox automation run—where build, health, and coverage phases were skipped as `environment-limited`—into a hardware replay that generates full packaging, health, and coverage exports for the audit ledger. 【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L13-L30】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout` |

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
> **Codex sandbox dependency limits.** When Stage A or Stage B rehearsals require GPUs, DAW plugins, or external connectors that the Codex sandbox cannot provide, follow [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints). Mark affected tests as `environment-limited`, capture the skipped command output in the alpha bundle, and log the pending validation in change notes. Escalate hardware-required follow-ups through the operator risk queue in [PROJECT_STATUS.md](PROJECT_STATUS.md#stage-c-planning-snapshot) and align messaging with the sandbox-to-hardware bridge plan documented in [roadmap.md](#stage-g-sandbox-to-hardware-bridge-validation).

> [!NOTE]
> **Sandbox audit (2025-09-27).** The latest Stage A sweep in `logs/alpha_gate/20250927T235425Z/` recorded missing build tooling, connector probes returning `503`, and `pytest.ini` coverage hooks failing without `pytest-cov`, so coverage gating remains deferred to the reserved hardware rehearsal window.【F:logs/alpha_gate/20250927T235425Z/command_log.md†L1-L9】【F:logs/alpha_gate/20250927T235425Z/health_check_connectors.log†L1-L5】【F:logs/alpha_gate/20250927T235425Z/pytest_coverage.log†L1-L6】

### Stage B – Subsystem hardening

| Task | Owner | Objective | Step 0 Look-ahead | Next up | Sandbox guidance | Hardware replay ID |
| --- | --- | --- | --- | --- | --- | --- |
| **B1. Memory fabric load proof** | @memory-squad | Optimize spiral memory ingestion and sharding so alpha stories meet the ≤120 ms P95 retrieval target. | Provision the host with the Rust toolchain and Python development headers, compile the Neo-ABZU bundle via `cargo build -p neoabzu-memory --release`, and complete the vector DB scaling checklist alongside the charter’s connector mocks. | Replace the 2025-12-05 sandbox proof—running with `stubbed_bundle: true` and the `environment-limited: neoabzu optional bundle unavailable` warning—with a hardware replay that records native bundle latencies and zero sandbox overrides. 【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L63】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L22-L30】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_b/20251205T142355Z-stage_b1_memory_proof` |
| **B2. Sonic core rehearsal lock** | @audio-lab | Stabilize audio synthesis and avatar harmonics so the demo script runs end-to-end without dropouts. | Pair the updated modulation presets with Crown orchestration metrics, mirroring the Stage A outputs. | Extend the clean Stage B2 rehearsal (`20251001T214349Z`) with hardware telemetry captures so the refreshed readiness packet can retire the sandbox-only audio assumptions. 【F:logs/stage_b/20251001T214349Z-stage_b2_sonic_rehearsal/summary.json†L1-L84】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_b/20251001T214349Z-stage_b2_sonic_rehearsal` |
| **B3. Connector credential rotation** | @integration-guild | Refresh primary connector handshakes and authentication flows for alpha datasets. | Finalize the API credential rotation plan and prepare rehearsal stubs noted in the charter. | Promote the 2025-12-05 rotation run—currently tagged `environment-limited: MCP gateway offline`—to a hardware execution that publishes a cleared `stage_b_rotation_drills.jsonl` and updates the readiness bundle. 【F:logs/stage_b/20251205T160210Z-stage_b3_connector_rotation/summary.json†L1-L129】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L24-L33】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_b/20251205T160210Z-stage_b3_connector_rotation` |

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

| Task | Owner | Objective | Step 0 Look-ahead | Next up | Sandbox guidance | Hardware replay ID |
| --- | --- | --- | --- | --- | --- | --- |
| **C1. Exit checklist consolidation** | @release-ops | Deliver the release checklist, verification bundle, and rollback playbook required for the alpha exit gate. | Aggregate subsystem handoffs and monitoring dashboards so the checklist draft mirrors Stage A/B deliverables. | Incorporate the 2025-12-08 readiness review minutes and the scheduled 2025-12-12 gate-runner replay into the checklist updates so hardware follow-ups inherit the sandbox `environment-limited` callouts. 【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L35】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251212T160000Z-readiness_packet` |
| **C2. Demo storyline freeze** | @audio-lab | Finalize the demo script assets and rehearsal artifacts for stakeholder sign-off. | Confirm the Stage B rehearsal telemetry meets the drop-free requirement and align with modulation presets. | Stage C bundle now ingests the refreshed Stage B evidence manifest—`20251001T085114Z-stage_c2_demo_storyline` captures the zero-drop replay, references the packaged upload hints, and records the updated `session_01_media.tar.gz` checksum for doctrine reviewers. |【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L78】【F:evidence_manifests/stage-b-audio.json†L1-L77】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251001T085114Z-stage_c2_demo_storyline` |
| **C3. Readiness signal sync** | @ops-team | Compile the Alpha readiness packet summarizing boot success rates, replay fidelity, and subsystem metrics. | Pull the latest telemetry from Stage A and Stage B tasks, update `PROJECT_STATUS.md` with outstanding risks, and embed the sandbox-to-hardware rehearsal bridge notes required by [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). | Reference both readiness bundles (`20251001T010101Z` and `20251205T193000Z`), plus the 2025-12-08 minutes that codify hardware follow-ups, so reviewers see how the sandbox skips (`environment-limited: MCP gateway offline`) will clear. 【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L33】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L35】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251205T193000Z-readiness_packet` |
| **C4. Operator MCP drills** | @ops-team | Land `OperatorMCPAdapter` for `operator_api`/`operator_upload` and confirm Stage B parity with `crown_handshake`. | Run `scripts/stage_b_smoke.py` to log the 48-hour credential rotation drill for each connector and archive the results under `logs/stage_b_rotation_drills.jsonl`, highlighting the successive windows `20251205T160210Z-PT48H`, `20250926T180300Z-PT48H`, `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20251024T174210Z-PT48H`, and the refreshed `20251001T093213Z-PT48H` ledger entries during roadmap syncs. | Promote the sandbox MCP drill (`environment-limited: MCP gateway offline`) to hardware during the 2025-12-12 replay, attach fresh handshake/heartbeat payloads, and update the readiness packet minutes with cleared credential statuses. 【F:logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json†L1-L12】【F:logs/stage_b_rotation_drills.jsonl†L70-L115】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L18-L33】 | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json` |

#### Stage C outcome recap (2025-10-01 – 2025-10-31)

- **Readiness bundle:** `logs/stage_c/20251001T010101Z-readiness_packet/` consolidates Stage A environment-limited gaps, the Stage B rehearsal ledger, and the Stage C MCP parity trial, keeping the gate-runner hardware replay blocked until the 2025-10-02 slot completes.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L2-L195】
- **Readiness refresh (2025-12-05):** `logs/stage_c/20251205T193000Z-readiness_packet/` records the latest sandbox bundle, notes the `environment-limited: MCP gateway offline` status for connector drills, and schedules the 2025-12-08 readiness review plus the 2025-12-12 gate-runner hardware replay.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L33】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L1-L12】
- **Demo storyline freeze:** The Stage C2 scripted replay locked the stakeholder narrative to the Stage B asset manifest, replayed all cues with zero dropouts, and captured the refreshed `session_01_media.tar.gz` checksum for doctrine reviewers.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L123】
- **Operator MCP drill:** The Stage C4 parity drill logged matching REST↔gRPC checksums, credential windows, and accepted contexts while flagging missing heartbeat payloads that the hardware replay must restore.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】
- **Residual hardware work:** Packaging/coverage transcripts still need a gate-runner replay, and emotional telemetry remains under sandbox overrides until the Neo-APSU migration closes the gap.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L35】【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L20-L29】
- **Cross-team review outcome (2025-12-08 16:00 UTC):** Minutes attached to the readiness packet list the attending leads, confirm the gate-runner-02 replay on 2025-12-12, and direct teams to propagate the sandbox skip strings into roadmap, PROJECT_STATUS, and PR summaries until hardware evidence clears the gaps.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L35】

> [!UPCOMING]
> **Readiness review:** 2025-10-04 16:00 UTC (facilitator: @release-ops) to walk the Stage C recap and introduce Stage D/E entry and exit criteria. Publish minutes to `logs/stage_c/20251004T160000Z-readiness_review/minutes.md` and link them inside `logs/stage_c/20251001T010101Z-readiness_packet/updates/` so downstream squads ingest the roadmap changes with the refreshed packet.

#### Beta bridge transport parity drill

- `logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json` captures the REST handshake accepted contexts, rotation window, and checksum for the operator beta bridge, matching the Stage C readiness targets.【F:logs/stage_c/20251031T000000Z-test/rest_handshake_with_expiry.json†L1-L41】
- The gRPC trial handshake mirrors the same session metadata and parity checksum under `logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json`, confirming transport equivalence ahead of pilot rollout.【F:logs/stage_c/20251031T000000Z-test/grpc_trial_handshake.json†L1-L71】
- `logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json` shows no payload differences and reports matching checksums, locking the beta bridge handshake scope before connector expansion.【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L11】
- The Stage C summary exposes the handshake artifact bundle while flagging `heartbeat_emitted: false`; the new connector monitoring payload now surfaces missing REST/gRPC latency and heartbeat alerts so the beta pilot can close instrumentation gaps prior to widening access.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/connectors/test_operator_mcp_adapter.py†L81-L106】

Stage C planners should review the Sonic Core optional component inventory and
the rehearsal evidence packet before go/no-go reviews so degraded audio or
avatar fidelity is flagged early for demo stakeholders.【F:docs/sonic_core_harmonics.md†L23-L51】【F:logs/stage_b_rehearsal_packet.json†L217-L344】

### Stage D – Production bridge

| Objective | Owner | Entry Criteria | Exit Criteria | Sandbox guidance | Hardware replay ID |
| --- | --- | --- | --- | --- | --- |
| Replay Stage C readiness bundle on hardware. | @ops-team | Stage C1 exit checklist schedules the 2025-12-12 gate-runner-02 parity sweep; readiness packet `logs/stage_c/20251212T160000Z-readiness_packet/` consolidates the manifest (`sha256 0ffb56ae01c4bc0672682f573962e05c796d5a53a0fc4cd37b5e26f50cb8ea97`), demo telemetry (`sha256 7150d6e459569c5a0f57b03dc5189a5e2116ecde5a959966cad8901130b66d06`), and MCP drill payloads (`sha256 2ad9b4add591862446626754b86b0d1c41a74ea4c1d31199e0a7e436472a67bb`/`b87c14920398b44479f3aca76dc5bd752a3147beedfe8216371d5c0000351bc5`) while flagging sandbox deferrals for `/alpha/stage-b3-connector-rotation` and `/alpha/stage-c4-operator-mcp-drill`. | Gate-runner replay captures parity diffs, refreshed checksums, checklist attachments, and updated review minutes in the Stage D ledger before clearing `environment-limited` skips. | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251212T160000Z-readiness_packet` |
| Promote Neo-APSU services with sandbox parity. | @neoabzu-core | Stage B rotation ledger and Stage C parity drill provide checksum, rotation, and context baselines for `operator_api`, `operator_upload`, and `crown_handshake`. | Hardware rollout publishes crate fingerprints, connector rotation receipts, and parity diffs that match the sandbox bundle before widening access. | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` |
| Extend transport telemetry dashboards to hardware spans. | @release-ops | Sandbox Grafana board and Stage C handshake diff demonstrate transport parity but highlight missing heartbeat metrics. | Production bridge emits latency/heartbeat telemetry with REST↔gRPC parity diffs attached to readiness minutes and dashboards for review. | [Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints); [Project Status](PROJECT_STATUS.md#codex-sandbox-constraints) | `logs/stage_c/20251031T000000Z-test/summary.json` |

> [!TIP]
> Stage D inherits the sandbox-to-hardware bridge instructions from [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). Rehearsal bundles should mirror the Stage C ledger structure so downstream auditors replay parity results without bespoke tooling.

Recent sandbox remediation captured an explicit before/after of the Stage B1 memory proof in `logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/`. The baseline run remained stubbed (`environment_mode="sandbox"`) with the optional bundle, while the post-rebuild metrics show the native `neoabzu_memory` crate exporting hardware-grade readiness figures (`environment_mode="hardware"`) alongside sandbox override flags for the remaining shims.【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/before/summary.json†L1-L32】【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L1-L38】 Stage D reviewers should pull these snapshots into the bridge ledger so parity packets inherit the hardware/native distinction.

The emotional telemetry path is still fronted by sandbox shims, as shown by the persisted `emotional_state` override in the refreshed summary; clearing that flag requires replaying the load proof on the gate-runner hardware before Stage D can certify aura logging for the bridge.【F:logs/stage_b/20250929T210655Z-stage_b1_memory_refresh/after/summary.json†L20-L29】

### Stage E – Transport/beta readiness

| Objective | Owner | Entry Criteria | Exit Criteria | Hardware Replay Reference |
| --- | --- | --- | --- | --- |
| Lock REST↔gRPC parity as a beta gate. | @release-ops | Stage C parity drill and Stage E readiness snapshot confirm checksum matches while flagging missing latency metrics. | Weekly beta reviews include checksum-matched trace bundles, contract test results tied to Grafana dashboards with hardware spans, and the recorded sandbox exports under `tests/fixtures/transport_parity/`. | Replay the Stage C handshake bundle during hardware rehearsals, refresh the Stage E JSON exports, and attach the updated traces to `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/` before beta sign-off.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】【F:tests/transport_parity/test_recorded_contracts.py†L1-L209】【F:monitoring/operator_transport_pilot.md†L54-L105】 |
| Restore connector heartbeat telemetry. | @integration-guild | Stage C bundle and Stage E readiness report both show `heartbeat_emitted: false` and missing latency metrics for operator, upload, and Crown connectors. | Hardware replay exports heartbeat payloads and latency series for all connectors, updating the readiness packet and Grafana dashboards. | Capture heartbeat payloads during the gate-runner replay and publish them alongside the Stage E connector traces for downstream squads.【F:logs/stage_c/20251031T000000Z-test/summary.json†L7-L50】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L34-L115】【F:monitoring/operator_transport_pilot.md†L1-L84】 |
| Document beta governance & approvals. | @qa-alliance | Stage C readiness minutes capture conditional GO status pending hardware reruns; beta launch plan references transport governance requirements. | Beta readiness packet includes updated minutes, sign-offs, and governance checklist entries aligned with hardware parity evidence. | Append the 2025-10-04 readiness review minutes and subsequent approvals to the Stage C packet before circulating the beta launch governance brief.【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】【F:docs/releases/beta_launch_plan.md†L47-L76】 |

Stage E extends the Stage C transport pilot: contract tests and dashboards now act as beta gatekeepers, and the weekly review agenda should add the Stage D bridge ledger alongside the existing parity drill recap. The Stage E snapshot at `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json` confirms checksum-matched parity traces for `operator_api`, `operator_upload`, and `crown_handshake` while flagging the sandbox heartbeat gaps and recording the shared telemetry hash (`30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8`) for dashboard verification.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L20-L87】【F:tests/transport_parity/test_recorded_contracts.py†L1-L209】 Continuous reviews should keep the dashboard URL (`https://grafana.ops.abzu.dev/d/operator-transport-parity/continuous-stage-e`) in the readiness minutes until heartbeat latency lands in the sandbox feed and should cite the recorded sandbox exports plus the beta rehearsal template when sharing evidence bundles.【F:monitoring/operator_transport_pilot.md†L54-L105】【F:tests/fixtures/transport_parity/operator_api_stage_e.json†L1-L138】【F:docs/releases/beta_rehearsal_template.md†L1-L120】

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

### Stage F – Hardware replay soak entry criteria

Stage F promotions remain blocked until sandbox evidence and hardware access
align. Use this checklist before attempting a Stage F soak handoff:

| Entry requirement | Owner | Evidence bundle | Notes |
| --- | --- | --- | --- |
| Sandbox evidence bundle consolidated | @qa-alliance | `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` + `logs/stage_b_rotation_drills.jsonl` + `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json` | Confirm the latest sandbox artifacts are staged together before requesting hardware replay.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_b_rotation_drills.jsonl†L12-L115】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】 |
| Gate-runner hardware window reserved | @ops-team | Stage C1 exit checklist + readiness minutes | Ensure the scheduled window covers every Neo-APSU module listed in the Stage F hardware replay plan before the soak begins.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】【F:docs/stage_f_hardware_replay_plan.md†L6-L54】 |
| Automation hook prepared | @neoabzu-core | `scripts/run_stage_f_replay.py` | Script currently emits an environment-limited warning; update with hardware orchestration steps once access is restored to avoid silent promotions.【F:scripts/run_stage_f_replay.py†L1-L36】 |

Document Stage F readiness using the dedicated hardware replay plan so roadmap
and PROJECT_STATUS stay synchronized on the sandbox inputs, scheduled hardware
windows, and required Neo-APSU validations before the soak window opens.【F:docs/stage_f_hardware_replay_plan.md†L1-L73】

### Stage G – Sandbox-to-hardware bridge validation

| Task | Owner | Hardware Validation Owner | Rollback Drill | Evidence Bundling |
| --- | --- | --- | --- | --- |
| **G1. Gate-runner parity replay** | @ops-team | @infrastructure-hardware | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/rollback_drill.md` rehearses the sandbox-first rollback that disables `gate_runner_enabled` and drains sessions via `operator_api` before resuming hardware once parity recovers. | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/parity_diff.json` binds the Stage C readiness bundle hash to the hardware replay with approvals in `approvals.yaml`. |
| **G2. Neo-APSU services parity** | @neoabzu-core | @neoabzu-core | `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/rollback_drill.md` walks the control-plane/workspace rollback using `scripts/stage_b_smoke.py` against the Stage B rotation ledger before re-enabling hardware. | `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/parity_diff.json` and `transport_contract.json` capture checksum matches, fallback events, and heartbeat recovery with signatures in `approvals.yaml`. |
| **G3. Evidence bundle stitching** | @qa-alliance | @ops-team | Rollback confirmation references the operator console export and sandbox replay noted in the Stage A/C readiness bundles to ensure gate-runner and Neo-APSU drills fall back to sandbox telemetry without data loss. | `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json` and `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json` enumerate bundle hashes aligned with [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment). |

Stage G maps the sandbox-to-hardware bridge directives from The Absolute Protocol directly into the roadmap. Hardware rehearsals must cite the Stage C readiness minutes and bundle hashes, attach rollback transcripts, and archive approvals from the operator lead, hardware owner, and QA reviewer before promoting later bridges.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/summary.json†L1-L13】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml†L1-L12】【F:docs/The_Absolute_Protocol.md†L54-L114】 Weekly reviews should confirm the `parity_diff.json` artifacts stay in sync with `logs/stage_c/20251001T010101Z-readiness_packet/` references and that rollback drills remain current before opening the production bridge window.

## Maintenance

Update this roadmap and `CHANGELOG.md` whenever a milestone is completed to record progress and guide future planning. Documentary additions such as [banana_rater.md](banana_rater.md) should be cross-linked when new evaluation flows launch. GA upkeep is governed by the LTS cadence in [`docs/lts/ga_lts_plan.md`](lts/ga_lts_plan.md), and quarterly reviews must refresh the doctrine hashes listed in [`docs/doctrine_index.md`](doctrine_index.md).
