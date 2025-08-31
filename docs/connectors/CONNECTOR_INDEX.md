# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version,
primary service endpoints, linked agents, and current status. Operator interface
entries detail the supported chat, file, image, audio, and video flows. Update
this index whenever a connector's interface changes. For shared patterns across
connectors see the [Connector Overview](README.md). This index is
cross‑referenced from [Key Documents](../KEY_DOCUMENTS.md) and
[The Absolute Protocol](../The_Absolute_Protocol.md).

| id | purpose | version | auth | endpoints | linked agents | status |
| --- | --- | --- | --- | --- | --- | --- |
| `webrtc` | real-time avatar streaming bridge for audio/video | 0.3.2 | JWT | `POST /call` | Nazarick Web Console | Experimental |
| `operator_upload` | operator asset upload API for files, images, audio, and video | 0.3.2 | Bearer | `POST /operator/upload` | RAZAR | Experimental |
| `crown_ws` | Crown WebSocket diagnostics channel for chat commands | 0.1.0 | Bearer | `WS /crown_link`, `POST /glm-command` | Crown | Experimental |
| `operator_api` | operator chat command dispatch | 0.3.2 | Bearer | `POST /operator/command` | Orchestration Master | Experimental |
| `open_web_ui` | browser-based console interface for chat | 0.1.0 | Bearer | `POST /glm-command` | Crown | Experimental |
| `telegram_bot` | Telegram channel relay for chat | 0.1.0 | Bot token | `POST /telegram/webhook` | Nazarick Agents | Experimental |
| `primordials_api` | metrics bridge to Primordials service | 0.1.1 | Bearer | `POST /metrics`, `GET /health` | Primordials | Experimental |
| `narrative_api` | narrative retrieval and stream | 0.1.0 | Bearer | `GET /story/log`, `GET /story/stream` | vector_memory | Experimental |
