# MCP Connectors

Assessment of tools and services for Model Context Protocol integration.

## Contribution Guidelines

Any pull request adding a connector must append its specification here with
heartbeat and health details.

## Decision Matrix

| Tool/Service | MCP Ready | Integration Effort | Notes |
| --- | --- | --- | --- |
| Slack Events API | Partial | Medium | Webhook interface fits MCP event model; requires auth wrapper. |
| GitHub Actions | No | High | Needs job runner bridge and context mapping to MCP schemas. |
| Notion API | Partial | Medium | Structured blocks align with MCP context; subject to rate limits. |
| LangChain | Yes | Low | Community adapter exposes chains over MCP. |
| Open WebUI | Yes | Low | Bundled MCP bridge for local models. |

## Integration Roadmap

1. Prototype Slack and Open WebUI connectors with heartbeat telemetry.
2. Add Notion and LangChain adapters, validating context registration.
3. Expand to GitHub Actions and publish reference implementations.

## Stage B MCP rehearsal catalog (2025-09-21)

Stage B rehearsals refreshed the catalog with live handshake transcripts and
credential rotation drills for the operator and Crown adapters. The table below
captures the negotiated capabilities, verified session windows, and the
rotation metadata recorded in the latest rehearsal export. Links point to the
archived artifacts maintained under `logs/stage_b/` for audit traceability.

| Connector | Module | Handshake snapshot | Rotation status | Drill outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| `operator_api_stage_b` | `connectors.operator_api_stage_b` | Version `0.1.0` handshake accepted context `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `command`; session `stage-b-session` authenticated with credential expiry `2025-09-23T12:25:30Z`. | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `operator`; rotation ledger also recorded the `12:24:53Z` preflight attempt. | Stage B smoke `20250921T122529Z` emitted handshake + heartbeat; doctrine note requiring adapter status added to the catalog. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b/20250921T122529Z/rotation_drills.json) |
| `operator_upload_stage_b` | `connectors.operator_upload_stage_b` | Version `0.1.0` handshake mirrored `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `upload`; operator session reuse confirmed (`stage-b-session` shared). | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `operator-upload`. | Stage B smoke `20250921T122529Z` reused the operator session and recorded heartbeat telemetry; catalog update synchronizes doctrine. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b/20250921T122529Z/rotation_drills.json) |
| `crown_handshake_stage_b` | `connectors.crown_handshake_stage_b` | Version `0.1.0` handshake confirmed `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `mission-brief`; Stage B smoke surfaced `crown_handshake` version `0.2.5`. | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `crown`. | Stage B smoke `20250921T122529Z` appended rotation drills for the Crown bridge alongside operator entries. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b/20250921T122529Z/rotation_drills.json) |
| `neo_apsu_connector_template` | `connectors.neo_apsu_connector_template` | Template echo during Stage B smoke accepted context `stage-b-rehearsal` with channels `handshake`, `heartbeat`; capabilities `register`, `telemetry`. | `last_rotated` `2025-09-21T12:25:29Z`, window `PT48H`, hot swap supported, token hint `local`. | Stage B smoke `20250921T122529Z` validated template metadata for downstream connector authors. | [Smoke handshake echo](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) |

Backlinks: [MCP Gateway Overview](mcp_overview.md)
