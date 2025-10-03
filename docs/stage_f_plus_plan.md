# Stage F+ Execution Plan

_Updated: 2025-12-18_

This plan expands the roadmap view for Stage F through Stage H so weekly reviews
have a single reference for hardware adoption goals, exit criteria, and evidence
handoffs. Every stage ties back to the [readiness ledger](readiness_ledger.md)
and the sandbox policy in [The Absolute Protocol](The_Absolute_Protocol.md#codex-sandbox-constraints)
to keep Codex-only skips visible until hardware replay closes the gaps.

## Stage F – Hardware replay soak alignment

- **Goals.** Deliver a coordinated soak window that replays the Stage C readiness
  packet, Stage E transport traces, and Stage B rotation ledger on hardware while
  documenting every sandbox-only deferral.
- **Entry criteria.**
  - Sandbox artifacts stitched together and cataloged in the readiness ledger
    with owners and remediation notes.
  - Gate-runner hardware slot booked and mirrored in the readiness minutes.
  - Automation hooks upgraded to log sandbox policy references for each
    `environment-limited` skip in accordance with The Absolute Protocol.
- **Exit criteria.**
  - Gate-runner replay exports checksum-matched bundles for the Stage C packet,
    Stage B rotation ledger, and Stage E transport traces, each tagged with the
    readiness ledger item that tracked the risk.
  - All soak evidence references The Absolute Protocol sandbox policy section
    plus the exact skip string being retired.
- **Required evidence.** Gate-runner parity diffs, MCP handshake/heartbeat
  captures, Stage E dashboard hash confirmation, and signed readiness minutes
  linking back to the ledger rows.
- **Responsible teams.** @ops-team (hardware orchestration), @neoabzu-core
  (service parity), @qa-alliance (evidence stitching).

## Stage G – Sandbox-to-hardware bridge validation

- **Goals.** Validate that sandbox replay hashes, rollback drills, and parity
  telemetry survive the hardware bridge while remaining traceable to the
  readiness ledger and sandbox policy directives.
- **Entry criteria.**
  - Stage F soak summary logged in the readiness ledger with updated residual
    risks and sandbox policy citations.
  - Hardware bridge playbooks aligned with The Absolute Protocol
    stage-alignment guidance and signed off in roadmap/PROJECT_STATUS updates.
- **Exit criteria.**
  - Gate-runner parity bundle and Neo-APSU parity bundle both capture approvals
    tying hardware evidence to the ledger rows and sandbox policy references.
  - Rollback drills execute without divergence and document how sandbox traces
    are restored per The Absolute Protocol guidance.
- **Required evidence.** Hardware parity diffs, rollback transcripts, updated
  readiness ledger entries, and synchronized roadmap/status excerpts pointing to
  sandbox policy clauses.
- **Responsible teams.** @ops-team, @neoabzu-core, @qa-alliance, with @release-ops
  confirming that readiness ledger hashes match the sandbox policy callouts.

## Stage H – Production adoption and LTS cutover

- **Goals.** Promote the GA cutover with verifiable lineage from Stage G
  approvals, readiness ledger closures, and sandbox policy compliance.
- **Entry criteria.**
  - Stage G bridge report archived in the readiness ledger with all sandbox
    deferrals marked resolved or migrated to GA tracking.
  - Incident response, rollback, and telemetry playbooks refreshed to cite
    The Absolute Protocol sandbox policy and bridge clauses.
- **Exit criteria.**
  - GA readiness packet logs final hardware telemetry hashes alongside the
    readiness ledger closure notes and sandbox policy references.
  - LTS cadence documentation confirms future hardware audits can replay the
    retired sandbox skips using the readiness ledger history.
- **Required evidence.** GA hardware cutover bundle, updated readiness ledger
  closure entries, LTS governance checklist with sandbox policy citations, and
  signed approvals from production, operations, and QA leads.
- **Responsible teams.** @release-ops (GA governance), @operations-lead
  (production telemetry), @qa-alliance (doctrine integrity), @neoabzu-core
  (Neo-APSU stewardship).
