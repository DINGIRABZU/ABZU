# Operator MCP Adoption Audit

This audit captures the work required to migrate the operator connectors to the
`neo_apsu_connector_template` handshake, heartbeat, and doctrine patterns.

## Current State

- `operator_api` exposes `POST /operator/command` and `POST /operator/upload`
  without an MCP handshake or Stage B context negotiation.
- File uploads and metadata relays are dispatched through
  `OperatorDispatcher` with no credential rotation checks.
- Heartbeat emission is only available through WebSocket broadcasts; there is no
  connector-level pulse aligned with the Stage B rehearsal schema.

## Gaps Relative to the Template

| Area | Template Expectation | Operator Connector Gap |
| --- | --- | --- |
| Handshake | Capability payload negotiated via `/handshake` with Stage B context enforcement. | No handshake route; bearer token assumed by FastAPI route handler. |
| Heartbeat | `send_heartbeat` enforces chakra, cycle counter, Stage B context, and credential expiry metadata. | Operator endpoints provide no heartbeat emitter or credential expiry tracking. |
| Doctrine | Registry alignment validated against `component_index.json`, connector index schema links, and credential rotation windows. | `operator_api` entry references FastAPI module only; no MCP schema, rotation log, or Stage B rehearsal acceptance record. |

## Migration Tasks

1. Introduce an MCP adapter that wraps the existing command and upload flows,
   delegating handshake and heartbeat responsibilities to the template helpers.
2. Register the adapter in the component and connector indexes, linking the
   Stage B heartbeat schema once finalized.
3. Implement a rehearsal script that validates the operator adapters alongside
   `crown_handshake`, logging credential rotation drills within a 48‑hour window.
4. Update documentation to reflect MCP availability and Stage B rehearsal
   coverage, including migration guidance and roadmap checklists.
