# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version,
primary service endpoints, authentication method, current status, and
references to documentation and source code. Update this index whenever a
connector's interface changes. For shared patterns across connectors see the
[Connector Overview](README.md). This index is cross‑referenced from
[Key Documents](../KEY_DOCUMENTS.md) and [The Absolute Protocol](../The_Absolute_Protocol.md).

| id | purpose | version | endpoints | auth | status | docs | code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `operator_api` | operator command and upload interface | 0.2.0 | `POST /operator/command`, `POST /operator/upload` | Authorization header | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `webrtc` | real-time avatar streaming bridge | 0.2.0 | `POST /call` | JWT | Experimental | [Nazarick Web Console](../nazarick_web_console.md) | [webrtc_connector.py](../../connectors/webrtc_connector.py) |
| `primordials_api` | DeepSeek‑V3 orchestration service | 0.1.0 | `POST /invoke`, `POST /inspire`, `GET /health` | Internal | Experimental | [Primordials Service](../primordials_service.md) | — |
| `crown` | Crown WebSocket and GLM endpoints | 0.1.0 | `WS /crown_link` | None | Experimental | [Crown Agent Overview](../CROWN_OVERVIEW.md) | [crown_link.py](../../agents/razar/crown_link.py) |
| `future_service` | placeholder for upcoming connectors | 0.0.0 | `TBD` | `TBD` | Planned | — | — |
