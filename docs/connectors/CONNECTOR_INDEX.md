# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version, primary service endpoints, linked agents, authentication method, status, and links to source code and documentation. Operator interface entries detail the supported chat, file, image, audio, and video flows. Update this index whenever a connector's interface changes. For shared patterns across connectors see the [Connector Overview](README.md). This index is cross‑referenced from [Key Documents](../KEY_DOCUMENTS.md) and [The Absolute Protocol](../The_Absolute_Protocol.md).

| id | purpose | version | auth | endpoints | linked agents | status | code | docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `operator_api` | operator chat command dispatch | 0.3.2 | Bearer | `POST /operator/command` | Orchestration Master | experimental | [operator_api.py](../../operator_api.py) | [operator_protocol.md](../operator_protocol.md) |
| `operator_upload` | operator asset upload API for files, images, audio, and video | 0.3.2 | Bearer | `POST /operator/upload` | RAZAR | experimental | [operator_api.py](../../operator_api.py) | [operator_protocol.md](../operator_protocol.md) |
| `crown_ws` | Crown WebSocket diagnostics channel for chat commands | 0.2.2 | Bearer | `WS /crown_link`, `POST /glm-command` | Crown | experimental | [razar/crown_link.py](../../razar/crown_link.py) | [RAZAR_AGENT.md](../RAZAR_AGENT.md) |
| `webrtc` | real-time avatar streaming bridge for audio/video | 0.3.2 | JWT | `POST /call` | Nazarick Web Console | experimental | [connectors/webrtc_connector.py](../../connectors/webrtc_connector.py) | [nazarick_web_console.md](../nazarick_web_console.md) |
| `open_web_ui` | browser-based console interface for chat | 0.1.1 | Bearer | `POST /glm-command` | Crown | experimental | [server.py](../../server.py) | [open_web_ui.md](../open_web_ui.md) |
| `telegram_bot` | Telegram channel relay for chat | 0.1.0 | Bot token | `POST /telegram/webhook` | Nazarick Agents | experimental | [communication/telegram_bot.py](../../communication/telegram_bot.py) | [communication_interfaces.md](../communication_interfaces.md) |
| `primordials_api` | metrics bridge to Primordials service | 0.1.1 | Bearer | `POST /metrics`, `GET /health` | Primordials | experimental | [connectors/primordials_api.py](../../connectors/primordials_api.py) | [primordials_service.md](../primordials_service.md) |
| `narrative_api` | narrative retrieval and stream | 0.1.0 | Bearer | `GET /story/log`, `GET /story/stream` | vector_memory | experimental | [narrative_api.py](../../narrative_api.py) | [nazarick_narrative_system.md](../nazarick_narrative_system.md) |
| `future_connectors` | placeholder for upcoming integrations | TBD | TBD | TBD | TBD | planned | N/A | [README.md](README.md) |
