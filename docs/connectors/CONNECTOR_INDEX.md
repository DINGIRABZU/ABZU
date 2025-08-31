# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version,
primary service endpoints, authentication method, current status, and
references to documentation and source code. Update this index whenever a
connector's interface changes. For shared patterns across connectors see the
[Connector Overview](README.md). This index is cross‑referenced from
[Key Documents](../KEY_DOCUMENTS.md) and [The Absolute Protocol](../The_Absolute_Protocol.md).

| id | purpose | version | endpoints | auth | status | docs | code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `operator_command` | operator command interface | 0.3.2 | `POST /operator/command` | Bearer (`operator` role) | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `operator_upload` | operator asset upload API | 0.3.2 | `POST /operator/upload` | Bearer (`operator` role) | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `webrtc` | real-time avatar streaming bridge (configurable audio/video) | 0.3.2 | `POST /call` | JWT | Experimental | [Nazarick Web Console](../nazarick_web_console.md) | [webrtc_connector.py](../../connectors/webrtc_connector.py) |
| `primordials_api` | Primordials service metrics relay | 0.1.1 | `POST /metrics`, `GET /health` | Internal bearer | Experimental | [Primordials Service](../primordials_service.md) | [primordials_api.py](../../connectors/primordials_api.py) |
| `crown_ws` | Crown WebSocket diagnostics channel | 0.1.0 | `WS /crown_link`, `POST /glm-command` | None (WS), Bearer (`glm_command_token`) | Experimental | [Crown Agent Overview](../CROWN_OVERVIEW.md) | [crown_link.py](../../agents/razar/crown_link.py) |
| `future_services` | placeholder for upcoming connectors | 0.0.0 | `TBD` | `TBD` | Planned | — | — |
