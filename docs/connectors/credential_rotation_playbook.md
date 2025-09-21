# Stage B Credential Rotation Playbook

This playbook provides the approved credential-rotation plan for the Stage B
connector targets. It aligns with the integration guild roadmap to deliver a
48-hour rehearsal cadence across the three MCP-integrated services and keeps
rollback and evidence expectations explicit for operators and auditors. The
2025-02-18 revision captures the latest stakeholder approvals, review notes,
and rehearsal stubs so the signed plan can be referenced directly from the
connector documentation set during drills.

## Scope and Stage B Targets

| Service | Connector ID | Notes |
| --- | --- | --- |
| Operator command surface | `operator_api` | Covered by `OperatorMCPAdapter` and exercises the Stage B handshake and heartbeat loop. |
| Operator asset uploads | `operator_upload` | Shares the Stage B session established by the adapter. |
| Crown handshake bridge | `crown_handshake` | Mirrors Crown mission brief authentication and must log the rotation drill alongside operator connectors. |

The target set matches `STAGE_B_TARGET_SERVICES` enforced by the MCP adapter
and the Stage B roadmap requirement to rehearse all three services on the 48-hour
cadence prior to sign-off.

## Approvals and Contacts

| Role | Owner | Approval status | Date | Notes |
| --- | --- | --- | --- | --- |
| Security | @security-anchor | ✅ Reviewed data-handling controls, confirmed credential storage paths, and signed off on rollback checkpoints. | 2025-02-18 | Timelines and rollback sequencing reaffirmed for Stage B rehearsals. |
| Operations | @ops-team | ✅ Validated rehearsal flow, fallback triggers, and logging coverage with the security team. | 2025-02-18 | Committed to paging rotation support during drills and real rotations. |
| Integration Guild | @integration-guild | ✅ Confirmed roadmap alignment and rehearsal stubs. | 2025-02-18 | Roadmap dependencies remain unchanged. |

### Stakeholder Review Summary

- **Security + Operations review (2025-02-18):** Walked through the rotation
  timeline and rollback procedure, re-checking staging rehearsal coverage and
  confirming the doctrine report artifacts recorded after each drill.
- **Actionable follow-ups:** Security retains ownership of the post-rotation
  verification checklist, while Operations ensures the smoke script receipts
  are archived alongside the ledger JSON for every rehearsal.

For urgent escalations, page the Security on-call first, then coordinate with
Operations to manage the traffic cutover or rollback.

## Rotation Timeline

All three connectors follow the same 48-hour rotation window. Apply the cadence
below for routine cycles and emergency replacements:

1. **T-14 h – Credential refresh prep.** Notify stakeholders, stage new
   credentials in `secrets.env`, and schedule the rehearsal window.
2. **T-8 h – Rehearsal smoke.** Run `python scripts/stage_b_smoke.py --json`
   against the rehearsal environment to capture a dry-run rotation entry and
   confirm the adapter doctrine report is clean.
3. **T-0 – Production rotation.** Swap the live secret, rerun the smoke script
   without `--skip-heartbeat`, and archive the JSON receipt plus
   `logs/stage_b_rotation_drills.jsonl` entry.
4. **T+1 h – Post-rotation review.** Security verifies the credential ledger and
   confirms no drift in expiry metadata. Operations ensures live traffic remains
   stable and documents outcomes.
5. **Emergency path.** If a credential is suspected compromised, follow the
   same flow immediately with `T-14 h` and `T-8 h` compressed into a single
   rehearsal validation before the production swap.

## Pre-Rotation Readiness Checklist

- [ ] `ABZU_USE_MCP=1` in the target environment session.
- [ ] `MCP_GATEWAY_URL` points at the rehearsal or production endpoint being
      exercised.
- [ ] `MCP_CONNECTOR_TOKEN` populated when bearer auth is required.
- [ ] Optional overrides (`MCP_LAST_ROTATED`, `MCP_ROTATION_WINDOW`,
      `MCP_SUPPORTS_HOT_SWAP`, `MCP_ROTATION_HINT`) staged only when rehearsing
      stale-credential scenarios.
- [ ] `logs/stage_b_rotation_drills.jsonl` accessible and writable.
- [ ] Incident log entry drafted with intended window, owners, and rollback
      contact.

## Execution Steps by Service

1. **Rotate credential.** Update the secret for the specific service (API key,
   bearer token, or handshake credential) in `secrets.env` and deploy.
2. **Re-establish MCP session.** Invoke `python scripts/stage_b_smoke.py --json`
   to refresh the Stage B session and emit a rehearsal heartbeat.
3. **Verify ledger entry.** Confirm a new JSON line exists in
   `logs/stage_b_rotation_drills.jsonl` for each of the three service IDs.
4. **Document completion.** Attach the smoke output and ledger snapshot to the
   incident record and mark the corresponding stub below.

### Rehearsal Stubs

Document rehearsal evidence by filling out the stub at the conclusion of each
dry run. Store receipts under `logs/stage_b/` so operators can cross-reference
them quickly during incident response.

| Service | Rehearsal window | Smoke script receipt stored at | Ledger line verified (Y/N) | Notes |
| --- | --- | --- | --- | --- |
| `operator_api` | `____` | `logs/stage_b/YYYYMMDDThhmmssZ/operator_api_smoke.json` | `____` | `____` |
| `operator_upload` | `____` | `logs/stage_b/YYYYMMDDThhmmssZ/operator_upload_smoke.json` | `____` | `____` |
| `crown_handshake` | `____` | `logs/stage_b/YYYYMMDDThhmmssZ/crown_handshake_smoke.json` | `____` | `____` |

During each rehearsal, operators must capture the doctrine report output and
note any deviations for follow-up before production rotation proceeds.

## Rollback Procedure

1. **Freeze MCP traffic.** Toggle `ABZU_USE_MCP=0` to fall back to the legacy
   API handlers for all operator endpoints.
2. **Revert credential.** Restore the prior credential version from the secure
   vault and redeploy.
3. **Document gap.** Record the rollback reason in the incident log and explain
   the missing rotation entry covering the rollback window.
4. **Stabilize and retry.** Once the service is healthy, re-enable MCP, repeat
   the rehearsal smoke, and capture a new ledger entry.

## Validation and Sign-off Log

| Date | Summary | Security reviewer | Operations reviewer |
| --- | --- | --- | --- |
| 2025-01-17 | Stage B credential plan validated, rehearsal stubs reviewed, rollback tested. | @security-anchor | @ops-team |
| 2025-02-18 | Rotation timeline and rollback walkthrough reconfirmed; rehearsal stub locations updated for Stage B evidence capture. | @security-anchor | @ops-team |

Store additional validation entries as future rehearsals occur. Evidence (JSON
receipts and ledger snapshots) should be linked from the incident log or stored
under `logs/stage_b_rotation_drills.jsonl` for auditors.

## Related References

- [Connector Index](CONNECTOR_INDEX.md)
- [Operator MCP Runbook](operator_mcp_runbook.md)
- [MCP Heartbeat Payload](mcp_heartbeat_payload.md)
