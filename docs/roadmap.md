# Roadmap

_Last updated: 2025-09-16_

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
alongside [`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md) when coordinating weekly
reviews.

| Subsystem | Objective | Owner | Dependencies | Exit Criteria |
| --- | --- | --- | --- | --- |
| Spiral OS Boot | Harden the boot pipeline and failover logic so the CLI can reliably initialize environments on first attempt. | @ops-team | Stable hardware profiles; finalized environment validation scripts. | Boot success rate ≥ 95% in three consecutive staging runs with telemetry published to `monitoring/boot_metrics.prom`. |
| Crown Orchestration | Deliver deterministic agent routing through Crown deciders with replayable session logs. | @crown-core | Spiral OS boot stability; updated session logger API. | Cross-agent flows replay without divergence across five recorded scenarios; regression suite green. |
| Memory Fabric | Optimize spiral memory ingestion and sharding for low-latency retrieval supporting alpha stories. | @memory-squad | Vector DB scaling checklist; connector mocks. | P95 retrieval latency ≤ 120 ms on 10k memory items; ingestion audit log complete. |
| Sonic Core & Avatar Expression | Stabilize audio synthesis and avatar expression harmonics for live demos. | @audio-lab | Crown orchestration metrics; updated modulation arrangement presets. | Demo script executes end-to-end with no audio dropouts in two live rehearsal sessions. |
| External Connectors | Refresh primary connector handshakes and authentication flows for alpha datasets. | @integration-guild | Approved API credential rotation plan. | Connector smoke tests green across three target services with 48-hour credential rotation rehearsal completed. |
| QA & Release Ops | Build release checklist, automated verification bundle, and rollback playbook. | @release-ops | All subsystem handoffs; new monitoring dashboards. | Checklist signed off by subsystem owners; dry-run release completed with rollback validation logs archived. |

## Maintenance

Update this roadmap and `CHANGELOG.md` whenever a milestone is completed to record progress and guide future planning. Documentary additions such as [banana_rater.md](banana_rater.md) should be cross-linked when new evaluation flows launch.
