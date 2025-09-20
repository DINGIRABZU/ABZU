# Operator MCP Adoption Audit

This audit captures the work required to migrate the operator connectors to the
`neo_apsu_connector_template` handshake, heartbeat, and doctrine patterns. The
operational procedures that close the Stage B rehearsal loop now live in the
[Operator MCP Runbook](operator_mcp_runbook.md).

## Current State

- [`OperatorMCPAdapter`](../../connectors/operator_mcp_adapter.py) now wraps
  the `operator_api` and `operator_upload` flows, exposing the MCP
  `POST /handshake` exchange with Stage B context enforcement, heartbeat
  metadata (`credential_expiry`, chakra, and cycle counters), and the doctrine
  validation helpers.
- [`scripts/stage_b_smoke.py`](../../scripts/stage_b_smoke.py) exercises the
  adapter handshake, emits the Stage B rehearsal heartbeat (unless disabled
  with `--skip-heartbeat`), evaluates doctrine alignment, and records rotation
  drills for both operator connectors in
  [`logs/stage_b_rotation_drills.jsonl`](../../logs/stage_b_rotation_drills.jsonl).
- The operator connector entries in the
  [Connector Index](CONNECTOR_INDEX.md) remain tagged as “migrating (MCP adapter
  stub)” while the production rollout and monitoring hooks are staged.
- Nightly CI now runs the Stage B smoke checks with `ABZU_USE_MCP=1`, uploads
  the JSON drill receipts, and fails if the latest rotation is older than the
  [`ROTATION_WINDOW_HOURS`](../../connectors/operator_mcp_adapter.py) service
  level objective, surfacing actionable logs for the operator team.

## Automation & Alerting Expectations

The **Stage B operator MCP drill** job in
[`nightly_ci.yml`](../../.github/workflows/nightly_ci.yml) installs the
connector dependencies, executes `python scripts/stage_b_smoke.py --json`, and
stores the JSON output alongside the rotation ledger as GitHub artifacts. A
lightweight parser reuses `ROTATION_WINDOW_HOURS` to ensure the most recent
rotation record in [`logs/stage_b_rotation_drills.jsonl`](../../logs/stage_b_rotation_drills.jsonl)
is within the allowed window. When the log is missing, empty, or stale, the job
exits non-zero and the workflow highlights the failure. Operators should triage
any failure within one rotation window, update credentials as needed, rerun the
smoke script manually to confirm recovery, and close the incident once the next
scheduled run passes.

## Gaps Relative to the Template

| Area | Template Expectation | Remaining Gap |
| --- | --- | --- |
| Production integration | Adapter-enabled connectors route production traffic through the MCP handshake before command or upload execution. | `OperatorMCPAdapter` is implemented but still needs to be wired into the deployed `operator_api`/`operator_upload` services; the [Connector Index entries](CONNECTOR_INDEX.md) remain in the “migrating” state until rollout completes. |
| Automation & observability | Stage B smoke checks run on a schedule, persist drill receipts, and page owners when rotation windows lapse. | Scheduled nightly drill now enforces the rotation window and publishes artifacts; remaining work is to connect the workflow failures to paging for 24/7 response. |
| Runbook updates | Template connectors ship with an operations playbook covering MCP feature toggles, rotation review, and rollback. | Draft runbook published at [operator_mcp_runbook.md](operator_mcp_runbook.md); circulate with operators, incorporate rollout-specific notes, and graduate the connectors from “migrating” to “active.” |

## Migration Tasks

1. Promote the adapter into production by routing `operator_api` and
   `operator_upload` requests through the MCP handshake before invoking legacy
   FastAPI handlers.
2. Schedule `scripts/stage_b_smoke.py` in CI/operations rotations and monitor
   `logs/stage_b_rotation_drills.jsonl` for rotation expiry alerts.
3. Update the Connector Index once production traffic runs through the adapter
   and Stage B rehearsals are automated, graduating both entries from
   “migrating” to “active.”
4. Publish an operator runbook that documents the MCP feature toggles, rehearsal
   verification flow, and rollback steps for future releases.
