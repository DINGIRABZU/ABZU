# Roadmap

_Last updated: 2025-10-24_

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

> [!IMPORTANT]
> **Codex sandbox dependency limits.** When Stage A or Stage B rehearsals require GPUs, DAW plugins, or external connectors that the Codex sandbox cannot provide, mark affected tests as `environment-limited`, capture the skipped command output in the alpha bundle, and log the pending validation in change notes. Escalate hardware-required follow-ups through the operator risk queue in [PROJECT_STATUS.md](PROJECT_STATUS.md#stage-c-planning-snapshot) and align messaging with [The Absolute Protocol](The_Absolute_Protocol.md#stage-gate-alignment).

### Stage B – Subsystem hardening

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **B1. Memory fabric load proof** | @memory-squad | Optimize spiral memory ingestion and sharding so alpha stories meet the ≤120 ms P95 retrieval target. | Complete the vector DB scaling checklist and validate connector mocks highlighted in the charter dependencies. | Capture ingestion audit logs and publish latency measurements from a 10k-item dataset for readiness review. |
| **B2. Sonic core rehearsal lock** | @audio-lab | Stabilize audio synthesis and avatar harmonics so the demo script runs end-to-end without dropouts. | Pair the updated modulation presets with Crown orchestration metrics, mirroring the Stage A outputs. | Conduct two live rehearsal sessions and archive telemetry showing zero audio dropouts. |
| **B3. Connector credential rotation** | @integration-guild | Refresh primary connector handshakes and authentication flows for alpha datasets. | Finalize the API credential rotation plan and prepare rehearsal stubs noted in the charter. | Run smoke tests across the three target services and document the 48-hour rotation drill results. |

#### Future Stage – gRPC adoption milestone

| Scope | Trigger | Exit Criteria |
| --- | --- | --- |
| Broaden gRPC interfaces across operator, memory, and connector pathways using the NeoABZU vector service contract as the canonical service pattern. | Promote from Stage B once connector drills and memory rehearsals log stable Stage gate evidence bundles, enabling the gRPC rollout to inherit verified telemetry flows. | Stage gate evidence ledger includes gRPC request/response traces, NeoABZU vector service parity checks, and operator rehearsal sign-off showing mixed REST/gRPC fallbacks without regression. |

### Stage C – Alpha exit prep

| Task | Owner | Objective | Step 0 Look-ahead | Next up |
| --- | --- | --- | --- | --- |
| **C1. Exit checklist consolidation** | @release-ops | Deliver the release checklist, verification bundle, and rollback playbook required for the alpha exit gate. | Aggregate subsystem handoffs and monitoring dashboards so the checklist draft mirrors Stage A/B deliverables. | Execute the dry-run release and archive rollback validation logs for the go/no-go review. |
| **C2. Demo storyline freeze** | @audio-lab | Finalize the demo script assets and rehearsal artifacts for stakeholder sign-off. | Confirm the Stage B rehearsal telemetry meets the drop-free requirement and align with modulation presets. | Stage C bundle now ingests the latest Stage B media manifest so asset URIs and integrity hashes ride alongside the replay evidence before the final recording review.【3222c5†L1-L8】【1bb329†L1-L86】 |
| **C3. Readiness signal sync** | @ops-team | Compile the Alpha readiness packet summarizing boot success rates, replay fidelity, and subsystem metrics. | Pull the latest telemetry from Stage A and Stage B tasks, update `PROJECT_STATUS.md` with outstanding risks, and embed the sandbox-to-hardware rehearsal bridge notes required by [The Absolute Protocol](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge). | Host the cross-team readiness review and capture action items gating the beta planning kickoff. |
| **C4. Operator MCP drills** | @ops-team | Land `OperatorMCPAdapter` for `operator_api`/`operator_upload` and confirm Stage B parity with `crown_handshake`. | Run `scripts/stage_b_smoke.py` to log the 48-hour credential rotation drill for each connector and archive the results under `logs/stage_b_rotation_drills.jsonl`, highlighting the successive windows `20250926T180300Z-PT48H`, `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20251024T174210Z-PT48H`, and the baseline `20250922T101554Z-PT48H` during roadmap syncs. | Promote the operator connectors to the MCP adoption checklist once smoke runs stabilize and Track B3 acceptance is closed out. |

Stage C planners should review the Sonic Core optional component inventory and
the rehearsal evidence packet before go/no-go reviews so degraded audio or
avatar fidelity is flagged early for demo stakeholders.【F:docs/sonic_core_harmonics.md†L23-L51】【F:logs/stage_b_rehearsal_packet.json†L217-L344】

## Maintenance

Update this roadmap and `CHANGELOG.md` whenever a milestone is completed to record progress and guide future planning. Documentary additions such as [banana_rater.md](banana_rater.md) should be cross-linked when new evaluation flows launch.
