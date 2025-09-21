# Stage B Credential Rotation Playbook

This playbook provides the approved credential-rotation plan for the Stage B
connector targets. It aligns with the integration guild roadmap to deliver a
48-hour rehearsal cadence across the three MCP-integrated services and keeps
rollback and evidence expectations explicit for operators and auditors.

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

| Role | Owner | Approval status | Date |
| --- | --- | --- | --- |
| Security | @security-anchor | ✅ Reviewed data-handling controls and confirmed credential storage paths. | 2025-01-17 |
| Operations | @ops-team | ✅ Validated rehearsal flow, fallback triggers, and logging coverage. | 2025-01-17 |
| Integration Guild | @integration-guild | ✅ Confirmed roadmap alignment and rehearsal stubs. | 2025-01-17 |

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

| Service | Rehearsal window | Smoke script receipt stored at | Ledger line verified (Y/N) | Notes |
| --- | --- | --- | --- | --- |
| `operator_api` | `____` | `____` | `____` | `____` |
| `operator_upload` | `____` | `____` | `____` | `____` |
| `crown_handshake` | `____` | `____` | `____` | `____` |

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

Store additional validation entries as future rehearsals occur. Evidence (JSON
receipts and ledger snapshots) should be linked from the incident log or stored
under `logs/stage_b_rotation_drills.jsonl` for auditors.

## Related References

- [Connector Index](CONNECTOR_INDEX.md)
- [Operator MCP Runbook](operator_mcp_runbook.md)
- [MCP Heartbeat Payload](mcp_heartbeat_payload.md)
