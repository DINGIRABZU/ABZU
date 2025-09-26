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

## Stage B MCP rehearsal catalog (2025-09-22)

Stage B rehearsals refreshed the catalog with live handshake transcripts and
credential rotation drills for the operator and Crown adapters. Automated
health probes now run alongside the rehearsal scheduler, producing a
`health_checks.json` ledger so reviewers can see the latest `/health`
responses captured with Stage B credentials. The table below captures the
negotiated capabilities, verified session windows, rotation metadata, and
health probe evidence recorded in the latest export. Links point to the
archived artifacts maintained under `logs/stage_b/` for audit traceability.

| Connector | Module | Handshake snapshot | Rotation status | Drill outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| `operator_api_stage_b` | `connectors.operator_api_stage_b` | Version `0.1.0` handshake accepted context `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `command`; session `stage-b-session` authenticated with credential expiry `2025-09-28T18:03:00Z`. | `last_rotated` `2025-09-26T18:03:00Z`, window `PT48H`, window id `20250926T180300Z-PT48H`, hot swap supported, token hint `operator`; the ledger also retains the rehearsal windows `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and the refresh `20251024T174210Z-PT48H`. | Stage B smoke `20250921T122529Z` emitted handshake + heartbeat while the rotation ledger aggregates the successive windows under `logs/stage_b_rotation_drills.jsonl`; the acceptance drill `20250926T180250Z` copied the ledger beside the summary bundle. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b_rotation_drills.jsonl) · [Stage B3 summary](../logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json) |
| `operator_upload_stage_b` | `connectors.operator_upload_stage_b` | Version `0.1.0` handshake mirrored `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `upload`; operator session reuse confirmed (`stage-b-session` shared). | `last_rotated` `2025-09-26T18:03:00Z`, window `PT48H`, window id `20250926T180300Z-PT48H`, hot swap supported, token hint `operator-upload`; prior windows `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and `20251024T174210Z-PT48H` remain archived for audit. | Stage B smoke `20250921T122529Z` reused the operator session; the Stage B3 acceptance run `20250926T180250Z` packages the ledger alongside `logs/stage_b_rotation_drills.jsonl`. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b_rotation_drills.jsonl) · [Stage B3 summary](../logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json) |
| `crown_handshake_stage_b` | `connectors.crown_handshake_stage_b` | Version `0.1.0` handshake confirmed `stage-b-rehearsal` with channels `handshake`, `heartbeat`, `mission-brief`; Stage B smoke surfaced `crown_handshake` version `0.2.5`. | `last_rotated` `2025-09-26T18:03:00Z`, window `PT48H`, window id `20250926T180300Z-PT48H`, hot swap supported, token hint `crown`; ledger history includes the rehearsal windows `20250926T180231Z-PT48H`, `20250925T095833Z-PT48H`, `20250925T094604Z-PT48H`, `20250922T101554Z-PT48H`, and the refresh `20251024T174210Z-PT48H`. | Stage B smoke `20250921T122529Z` appended rotation drills; the rotation log maintains the successive windows under `logs/stage_b_rotation_drills.jsonl`, and the Stage B3 acceptance run `20250926T180250Z` archives the copied ledger beside the summary. | [Rehearsal packet](../logs/stage_b_rehearsal_packet.json) · [Smoke handshake](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation drills](../logs/stage_b_rotation_drills.jsonl) · [Stage B3 summary](../logs/stage_b/20250926T180250Z-stage_b3_connector_rotation/summary.json) |
| `neo_apsu_connector_template` | `connectors.neo_apsu_connector_template` | Template echo during Stage B smoke accepted context `stage-b-rehearsal` with channels `handshake`, `heartbeat`; capabilities `register`, `telemetry`. | `last_rotated` `2025-09-21T12:25:29Z`, window `PT48H`, hot swap supported, token hint `local`. | Stage B smoke `20250921T122529Z` validated template metadata for downstream connector authors. | [Smoke handshake echo](../logs/stage_b/20250921T122529Z/stage_b_smoke.json) |

Backlinks: [MCP Gateway Overview](mcp_overview.md)
