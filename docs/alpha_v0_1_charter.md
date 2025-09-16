# Alpha v0.1 Charter

_Last updated: 2025-09-16_

Alpha v0.1 readiness is listed as an upcoming milestone in
[ABSOLUTE_MILESTONES.md](ABSOLUTE_MILESTONES.md#upcoming-milestones) with a Q3 2025
target. This charter consolidates the subsystem deliverables, dependencies, and
acceptance criteria required to reach that milestone while reflecting the
current progress summarized in [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Scope and Objectives

- Deliver a reliable Spiral OS boot sequence and supporting CLI tools that align
  with the minimal workflow documented under Planned Releases in
  [PROJECT_STATUS.md](PROJECT_STATUS.md#planned-releases).
- Maintain deterministic Crown orchestration and sonic core pipelines so the
  Alpha demo script can run end-to-end, building on the recent logging and
  transformation refactors recorded in the Project Status report.
- Formalize release management and rollback paths so QA can sign off on the
  alpha drop with confidence.

## Subsystem Commitments

| Subsystem | Owner | Deliverable | Key Dependencies | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| Spiral OS Boot | @ops-team | Harden boot pipeline and failover logic for consistent first-attempt environment initialization. | Stable hardware profiles; validated environment scripts; sustained boot telemetry export. | Boot success rate ≥ 95% across three consecutive staging runs with metrics in `monitoring/boot_metrics.prom`. |
| Crown Orchestration | @crown-core | Deterministic agent routing with replayable session logs. | Spiral OS boot stability; refreshed session logger API; adherence to recent refactoring guidelines. | Five recorded cross-agent flows replay without divergence; regression suite passes. |
| Memory Fabric | @memory-squad | Low-latency spiral memory ingestion and sharding supporting alpha storytelling. | Vector DB scaling checklist; connector mocks; dependency on memory sharding baseline from Absolute milestones. | P95 retrieval latency ≤ 120 ms on 10k items; ingestion audit log complete. |
| Sonic Core & Avatar Expression | @audio-lab | Stable audio synthesis and avatar harmonics for live demos. | Crown orchestration metrics; updated modulation presets; Milestone VIII workstream. | Demo script completes twice without audio dropouts; rehearsal telemetry archived. |
| External Connectors | @integration-guild | Refreshed connector handshakes and auth flows for alpha datasets. | Approved credential rotation plan; optional dependency stubs tracked in Project Status. | Smoke tests green across three services; 48-hour credential rotation rehearsal recorded. |
| QA & Release Ops | @release-ops | Release checklist, verification bundle, and rollback playbook. | Subsystem handoffs; monitoring dashboards; coverage tooling path (coverage badge in Project Status). | Checklist signed off by subsystem owners; dry-run release with rollback validation logs archived. |

## Subsystem Notes and Interlocks

### Spiral OS Boot
- **Current signals:** Minimal environment validation tests pass with eight tests
  green, providing a baseline for further boot hardening (see the Project Status
  _Test Run_ section).
- **Execution focus:** Coordinate hardware profile documentation with the ops
  team and ensure telemetry exporters feed the `boot_metrics.prom` pipeline prior
  to staging rehearsals.

### Crown Orchestration
- **Current signals:** Session logging utilities were recently standardized,
  offering the replay foundation required for deterministic routing.
- **Execution focus:** Align decider updates with Spiral OS boot milestones to
  avoid regressions in first-attempt initialization.

### Memory Fabric
- **Current signals:** The Memory Sharding milestone in
  [ABSOLUTE_MILESTONES.md](ABSOLUTE_MILESTONES.md#past-milestones) established the
  storage blueprint that this work extends.
- **Execution focus:** Validate scaling checklists against connector mocks before
  enabling ingestion for alpha narratives.

### Sonic Core & Avatar Expression
- **Current signals:** Milestone VIII remains active in
  [PROJECT_STATUS.md](PROJECT_STATUS.md#active-tasks), underscoring the need to
  sync harmonics and avatar expression workstreams.
- **Execution focus:** Pair rehearsal telemetry collection with the updated
  modulation presets to hit drop-free demo runs.

### External Connectors
- **Current signals:** Optional dependency stubs are tracked as an active task in
  the Project Status report; connector updates should leverage that effort.
- **Execution focus:** Schedule rotation rehearsals alongside QA so audit logs
  are ready before the charter exit review.

### QA & Release Ops
- **Current signals:** Coverage exports remain at 1%, highlighting the need for
  the release verification bundle to supplement automated checks.
- **Execution focus:** Draft rollback playbooks in collaboration with subsystem
  owners, capturing the sign-off path required in the acceptance criteria.

## Cadence and Review

- Charter reviews occur bi-weekly during the Alpha readiness sync. Update this
  document in tandem with the roadmap whenever acceptance criteria shift.
- Upon meeting all acceptance criteria, update
  [PROJECT_STATUS.md](PROJECT_STATUS.md#planned-releases) and
  [ABSOLUTE_MILESTONES.md](ABSOLUTE_MILESTONES.md#upcoming-milestones) to reflect
  the milestone as complete and trigger the release checklist audit.
