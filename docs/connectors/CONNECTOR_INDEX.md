# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version, primary service endpoints, linked agents, authentication method, status, and links to source code, documentation, and a JSON or YAML schema describing the interface. Operator interface entries detail the supported chat, file, image, audio, and video flows. Update this index whenever a connector's interface changes. For shared patterns across connectors see the [Connector Overview](README.md). This index is cross‑referenced from [Key Documents](../KEY_DOCUMENTS.md) and [The Absolute Protocol](../The_Absolute_Protocol.md); see the [Connector Registry Protocol](../The_Absolute_Protocol.md#connector-registry-protocol) for the checklist.

For instructions on converting legacy API connectors to the Model Context Protocol,
refer to the [MCP Migration Guide](mcp_migration.md).

| id | purpose | version | auth | endpoints | linked agents | status | code | docs | schema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `operator_api` | operator chat command dispatch | 0.3.7 | Bearer | `POST /operator/command` | Orchestration Master | active (MCP flow live) | [operator_api.py](../../operator_api.py) | [operator_protocol.md](../operator_protocol.md), [operator_mcp_audit.md](operator_mcp_audit.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | N/A |
| `operator_upload` | operator asset upload API for files, images, audio, and video | 0.3.7 | Bearer | `POST /operator/upload` | RAZAR | active (MCP flow live) | [operator_api.py](../../operator_api.py) | [operator_protocol.md](../operator_protocol.md), [operator_mcp_audit.md](operator_mcp_audit.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | N/A |
| `crown_ws` | Crown WebSocket diagnostics channel for chat commands | 0.2.2 | Bearer | `WS /crown_link`, `POST /glm-command` | Crown | deprecated | [razar/crown_link.py](../../razar/crown_link.py) | [CROWN_OVERVIEW.md](../CROWN_OVERVIEW.md) | N/A |
| `crown_handshake` | RAZAR mission brief handshake with Crown | 0.2.4 | Bearer | `WS CROWN_WS_URL` | Crown | active | [razar/crown_handshake.py](../../razar/crown_handshake.py) | [CROWN_OVERVIEW.md](../CROWN_OVERVIEW.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | N/A |
| `webrtc` | real-time avatar streaming bridge for audio/video | 0.3.3 | JWT | `POST /call` | Nazarick Web Console | experimental | [connectors/webrtc_connector.py](../../connectors/webrtc_connector.py) | [nazarick_web_console.md](../nazarick_web_console.md) | N/A |
| `open_web_ui` | browser-based console interface for chat | 0.1.1 | Bearer | `POST /glm-command` | Crown | experimental | [server.py](../../server.py) | [open_web_ui.md](../open_web_ui.md) | N/A |
| `discord_bot` | Discord channel relay for chat | 0.3.0 | Bot token | Discord API | Nazarick Agents | experimental | [tools/bot_discord.py](../../tools/bot_discord.py) | [communication_interfaces.md](../communication_interfaces.md) | N/A |
| `telegram_bot` | Telegram channel relay for chat | 0.3.0 | Bot token | Telegram Bot API | Nazarick Agents | experimental | [tools/bot_telegram.py](../../tools/bot_telegram.py) | [communication_interfaces.md](../communication_interfaces.md) | N/A |
| `primordials_api` | metrics bridge to Primordials service | 0.1.1 | Bearer | `POST /metrics`, `GET /health` | Primordials | experimental | [connectors/primordials_api.py](../../connectors/primordials_api.py) | [primordials_service.md](../primordials_service.md) | [primordials_api.schema.json](../../schemas/primordials_api.schema.json) |
| `narrative_api` | narrative logging and stream | 0.2.0 (`__version__`) | Bearer | `POST /story`, `GET /story/log`, `GET /story/stream` | vector_memory | experimental | [narrative_api.py](../../narrative_api.py) | [nazarick_narrative_system.md](../nazarick_narrative_system.md) | N/A |
| `primordials_mcp` | MCP wrapper for Primordials metrics | 0.1.0 | Bearer | `POST /context/register`, `POST /primordials/metrics` | Primordials | experimental | [connectors/primordials_mcp.py](../../connectors/primordials_mcp.py) | [primordials_service.md](../primordials_service.md) | [primordials_api.schema.json](../../schemas/primordials_api.schema.json) |
| `narrative_mcp` | MCP wrapper for narrative logging | 0.1.0 | Bearer | `POST /context/register`, `POST /narrative/story` | vector_memory | experimental | [connectors/narrative_mcp.py](../../connectors/narrative_mcp.py) | [nazarick_narrative_system.md](../nazarick_narrative_system.md) | N/A |
| `avatar_broadcast` | broadcast avatar frames to Discord and Telegram | 0.1.0 | Bot token | Discord API, Telegram API | Discord, Telegram | experimental | [connectors/avatar_broadcast.py](../../connectors/avatar_broadcast.py) | N/A | N/A |
| `signal_bus` | cross-connector publish/subscribe bus | 0.3.0 | N/A | Redis/Kafka | all connectors | experimental | [connectors/signal_bus.py](../../connectors/signal_bus.py) | [README.md](README.md) | N/A |
| `mcp_gateway_example` | example MCP gateway connector | 0.2.0 | Configured | `POST /model/invoke` | internal models | experimental | [connectors/mcp_gateway_example.py](../../connectors/mcp_gateway_example.py) | [README.md](README.md) | N/A |
| `neo_apsu_connector_template` | template for new connectors | 0.2.0 | Bearer | `POST /handshake`, `POST /heartbeat` | MCP gateway | experimental | [connectors/neo_apsu_connector_template.py](../../connectors/neo_apsu_connector_template.py) | [mcp_capability_payload.md](mcp_capability_payload.md) | [mcp_heartbeat_payload.schema.json](../../schemas/mcp_heartbeat_payload.schema.json) |
| `operator_api_stage_b` | Stage B MCP handshake and heartbeat for operator commands | 0.1.0 | Bearer | `POST /handshake`, `POST /heartbeat` | Orchestration Master | experimental | [connectors/operator_api_stage_b.py](../../connectors/operator_api_stage_b.py) | [operator_mcp_runbook.md](operator_mcp_runbook.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | [mcp_heartbeat_payload.schema.json](../../schemas/mcp_heartbeat_payload.schema.json) |
| `operator_upload_stage_b` | Stage B MCP handshake and heartbeat for operator uploads | 0.1.0 | Bearer | `POST /handshake`, `POST /heartbeat` | RAZAR | experimental | [connectors/operator_upload_stage_b.py](../../connectors/operator_upload_stage_b.py) | [operator_mcp_runbook.md](operator_mcp_runbook.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | [mcp_heartbeat_payload.schema.json](../../schemas/mcp_heartbeat_payload.schema.json) |
| `crown_handshake_stage_b` | Stage B MCP handshake mirroring Crown mission briefs | 0.1.0 | Bearer | `POST /handshake`, `POST /heartbeat` | Crown | experimental | [connectors/crown_handshake_stage_b.py](../../connectors/crown_handshake_stage_b.py) | [operator_mcp_runbook.md](operator_mcp_runbook.md), [credential_rotation_playbook.md](credential_rotation_playbook.md) | [mcp_heartbeat_payload.schema.json](../../schemas/mcp_heartbeat_payload.schema.json) |

### Stage B MCP rehearsal evidence

Stage B rehearsals refreshed the MCP connector catalog with validated handshakes,
accepted contexts, and credential rotation telemetry. The artifacts below capture
the negotiated capabilities and rotation windows exercised during the latest run.

| Connector | Module | Contexts, channels, capabilities | Credential rotation | Evidence |
| --- | --- | --- | --- | --- |
| `operator_api_stage_b` | `connectors.operator_api_stage_b` | Context `stage-b-rehearsal` accepted with channels `handshake`, `heartbeat`, `command` and capabilities `register`, `telemetry`, `command`. | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `operator`; heartbeat credential expiry `2025-09-23T12:25:30Z`. | [Stage B rehearsal packet](../../logs/stage_b_rehearsal_packet.json) · [Stage B smoke (handshake & heartbeat)](../../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation summary](../../logs/stage_b/20250921T122529Z/rotation_drills.json) |
| `operator_upload_stage_b` | `connectors.operator_upload_stage_b` | Context `stage-b-rehearsal` accepted with channels `handshake`, `heartbeat`, `upload` and capabilities `register`, `telemetry`, `upload`. | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `operator-upload`; shares heartbeat expiry `2025-09-23T12:25:30Z`. | [Stage B rehearsal packet](../../logs/stage_b_rehearsal_packet.json) · [Stage B smoke (handshake & heartbeat)](../../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation summary](../../logs/stage_b/20250921T122529Z/rotation_drills.json) |
| `crown_handshake_stage_b` | `connectors.crown_handshake_stage_b` | Context `stage-b-rehearsal` accepted with channels `handshake`, `heartbeat`, `mission-brief` and capabilities `register`, `telemetry`, `mission-brief`. | `last_rotated` `2025-09-21T12:25:30Z`, window `PT48H`, hot swap supported, token hint `crown`; heartbeat credential expiry `2025-09-23T12:25:30Z`. | [Stage B rehearsal packet](../../logs/stage_b_rehearsal_packet.json) · [Stage B smoke (handshake & heartbeat)](../../logs/stage_b/20250921T122529Z/stage_b_smoke.json) · [Rotation summary](../../logs/stage_b/20250921T122529Z/rotation_drills.json) |

Rotation drills captured alongside the latest rehearsal confirm the operator
and Crown connectors rotated credentials on `2025-09-21T12:25:30Z`, maintaining
the declared 48-hour window for Stage B readiness. Review the append-only log at
[stage_b_rotation_drills.jsonl](../../logs/stage_b_rotation_drills.jsonl) for the
full drill history and cross-check the run-scoped export in
[`logs/stage_b/20250921T122529Z/rotation_drills.json`](../../logs/stage_b/20250921T122529Z/rotation_drills.json).

## MCP Migration Status

| connector | protocol | migration_notes |
| --- | --- | --- |
| `operator_api` | API → MCP | Production traffic uses `OperatorMCPAdapter` for startup handshake and live Stage B heartbeats. |
| `operator_upload` | API → MCP | Shares the live `OperatorMCPAdapter` session and heartbeat loop from `operator_api`. |
| `crown_ws` | API | deprecated; no migration planned |
| `crown_handshake` | API | evaluate MCP handshake |
| `webrtc` | API | streaming; MCP transport under review |
| `open_web_ui` | API | candidate for MCP gateway |
| `discord_bot` | MCP/API | uses MCP for GLM commands; Discord API remains |
| `telegram_bot` | MCP/API | uses MCP for GLM commands; Telegram API remains |
| `primordials_api` | API | external service requires REST; MCP wrapper `primordials_mcp` |
| `narrative_api` | API | MCP wrapper `narrative_mcp` available |
| `primordials_mcp` | MCP | wraps Primordials metrics over gateway |
| `narrative_mcp` | MCP | wraps narrative logging over gateway |
| `mcp_gateway_example` | MCP | reference implementation |

Backlinks: [Component Index](../component_index.md) | [Dependency Index](../dependency_index.md) | [Test Index](../test_index.md)
