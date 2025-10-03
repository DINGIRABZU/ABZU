# Stage D/E Bridge Review Agenda

This agenda prepares the Stage D hardware bridge and Stage E beta transport gate for weekly readiness reviews. Reference the [readiness ledger](../readiness_ledger.md#artifact-overview) when recording outcomes so parity artifacts remain discoverable.

## Discussion topics

1. **Readiness ledger reconciliation**  
   - Confirm Stage C replay artifacts logged in the ledger are linked to the upcoming hardware slot.  
   - Verify Stage D bridge watch items and Stage E telemetry gaps have updated timestamps and owners.
2. **Parity drill status**  
   - Review the latest REST↔gRPC parity logs, including checksum hashes and heartbeat telemetry.  
   - Capture dashboard URLs and compare against prior ledger snapshots to show progress.
3. **MCP rotation coverage**  
   - Examine the 48-hour rotation transcripts and credential expiry schedule.  
   - Highlight pending rotations that must land in the Stage D ledger before the beta go/no-go.
4. **Demo storyline bundle**  
   - Validate that the scripted demo bundle aligns with the Stage C readiness packet and includes sandbox vs hardware notes.  
   - Identify any environment-limited evidence and schedule hardware replays when required.
5. **Follow-up actions**  
   - Assign owners for missing artifacts, dashboard exports, or sign-offs.  
   - Ensure the readiness ledger is updated with due dates and evidence pointers.

## Decisions to capture

- Whether Stage D hardware replays unblock the outstanding readiness ledger entries.  
- Readiness of Stage E transport telemetry to graduate into beta cadence.  
- Approval to publish updated parity summaries or defer to the next gate-runner window.  
- Any environment-limited skips that must be documented in both the roadmap and PROJECT_STATUS updates.

Record each decision in the readiness ledger with links to the supporting artifacts and updated owners.

## Required evidence package

| Evidence type | Description | Ledger reference |
| --- | --- | --- |
| Parity logs | REST↔gRPC handshake diffs, checksum hashes, latency spans, and heartbeat telemetry exported from the latest rehearsal. | Add to the Stage D entry in the [readiness ledger](../readiness_ledger.md#stage-d-bridge-watch-items) and cross-link with the transport parity snapshot. |
| MCP rotation transcripts | Rotation schedules, credential expiry summaries, and MCP heartbeat payloads proving 48-hour coverage. | Attach to the Stage D ledger row and update the rotation ledger pointer in the [readiness ledger](../readiness_ledger.md#rotation-ledger). |
| Demo bundle | Scripted storyline export (telemetry, checklist attachments, review minutes) mapped back to the Stage C readiness packet. | Store under the Stage E evidence queue within the [readiness ledger](../readiness_ledger.md#stage-e-beta-gate) so beta reviewers inherit the same bundle IDs. |
| Evidence request forms | Completed templates from teams submitting sandbox or hardware proofs (see the [evidence request template](evidence_request_template.md)). | Link each submission under the relevant Stage D or Stage E ledger entry with owner, timestamp, and follow-up window. |

> **Reminder:** Update `docs/INDEX.md` and rerun documentation hooks after appending new evidence, ensuring all ledger references remain synchronized.
