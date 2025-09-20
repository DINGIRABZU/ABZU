# Operator MCP Adoption Audit

This audit captures the work required to migrate the operator connectors to the
`neo_apsu_connector_template` handshake, heartbeat, and doctrine patterns.

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

## Gaps Relative to the Template

| Area | Template Expectation | Remaining Gap |
| --- | --- | --- |
| Production integration | Adapter-enabled connectors route production traffic through the MCP handshake before command or upload execution. | `OperatorMCPAdapter` is implemented but still needs to be wired into the deployed `operator_api`/`operator_upload` services; the [Connector Index entries](CONNECTOR_INDEX.md) remain in the “migrating” state until rollout completes. |
| Automation & observability | Stage B smoke checks run on a schedule, persist drill receipts, and page owners when rotation windows lapse. | `scripts/stage_b_smoke.py` runs manually; integrate it into CI/ops rotations and define alerting around [`logs/stage_b_rotation_drills.jsonl`](../../logs/stage_b_rotation_drills.jsonl). |
| Runbook updates | Template connectors ship with an operations playbook covering MCP feature toggles, rotation review, and rollback. | Document production enablement steps and the Stage B rehearsal review loop so the operator team can graduate the connectors from “migrating” to “active.” |

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
