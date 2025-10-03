# Codex Lessons

The Codex sandbox forces contributors to operate with constrained tooling and
hardware. This knowledge base entry captures the recurring limitations,
experiments that failed inside the sandbox, the workarounds we rely on, and the
policies that evolved from those lessons. Review this page alongside
[`docs/documentation_protocol.md`](../documentation_protocol.md) and
[`docs/The_Absolute_Protocol.md`](../The_Absolute_Protocol.md#codex-sandbox-constraints)
before planning any new effort so the sandbox context is fully understood.

## Sandbox limitations

- **Hardware access gaps.** GPU acceleration, DAW plug-ins, FFmpeg, SoX, and the
  extended Neo-APSU harness are unavailable. Tests that require these assets must
  log the `environment-limited: <reason>` skip string and be scheduled for
  hardware replay via the readiness ledger.
- **Credentialed connectors.** Secrets needed for `/alpha/stage-b3-connector-rotation`
  and MCP parity drills are blocked in Codex. Sandbox runs can only verify mocks
  or dry-run scripts; production credentials stay quarantined until a gate-runner
  slot opens.
- **Packaging and coverage exports.** `python -m build`, `pytest-cov`, and
  release packaging utilities are missing. The roadmap, readiness packet, and PR
  summaries must note when automation phases are deferred for hardware replay.

## Failed attempts logged in the sandbox

| Attempt | Date | Outcome | Follow-up |
| --- | --- | --- | --- |
| Stage A automation replay | 2025-11-05 | `environment-limited: python -m build unavailable` halted the
  packaging phase and prevented coverage exports. | Re-run on hardware during the
  Stage D/E bridge slot with the tooling installed; attach updated bundles to the
  readiness packet. |
| Connector rotation rehearsal | 2025-12-05 | MCP gateway offline prevented credential refresh and
  heartbeat capture. | Schedule the `/alpha/stage-b3-connector-rotation` command
  on gate-runner-02 and archive refreshed handshake payloads. |
| Demo telemetry capture | 2025-12-05 | Media export deferred because FFmpeg/SoX are blocked. | Log the
  stub summary and replay the demo on hardware, capturing signed telemetry
  bundles for doctrine. |

## Workarounds and mitigations

- **Documented stubs.** Every deferred bundle must include a stub summary inside
  `logs/stage_c/` so auditors know which evidence is pending.
- **Readiness ledger tracking.** Each sandbox skip is mirrored in
  [`docs/readiness_ledger.md`](../readiness_ledger.md) with owner assignments and
  replay targets so no deferral gets lost between reviews.
- **Cross-team callouts.** Minutes in `logs/stage_c/20251205T193000Z-readiness_packet/`
  list the gate-runner slots reserved for clearing sandbox gaps. Link these
  minutes in change logs and doctrine updates to maintain visibility.

## Policy rationale

1. **Consistency for auditors.** Mirroring the `environment-limited` phrases in
   documentation, readiness packets, and PRs ensures audits trace sandbox-only
   runs without reinterpreting terminology.
2. **Hardware replay lineage.** The Absolute Protocol requires every sandbox
   deferral to point at an explicit hardware slot. Referencing the readiness
   ledger keeps that lineage visible to stage owners.
3. **Shared institutional memory.** Capturing lessons here reduces duplicate
   debugging attempts and gives future agents immediate context before modifying
   automation, connectors, or media tooling.

## How to contribute updates

- Append weekly summaries or decision records to
  [`change_log.md`](change_log.md) with links to the related pull requests or
  readiness ledger entries.
- Reference this page whenever sandbox constraints influence planning,
  documentation, or testing strategy.
- When hardware replays resolve a limitation, update both this document and the
  readiness ledger to retire outdated guidance.
