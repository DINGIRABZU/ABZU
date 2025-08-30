# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the version, primary service endpoints, authentication method, current status, and references to documentation and source code. For shared patterns across connectors see the [Connector Overview](README.md).

| id | version | service | endpoints | auth | status | docs | code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `webrtc` | 0.2.0 | WebRTC | `POST /call` | JWT | Experimental | [Nazarick Web Console](../nazarick_web_console.md) | [webrtc_connector.py](../../connectors/webrtc_connector.py) |
| `telegram_bot` | 0.1.0 | Telegram Bot API | Telegram API (polling) | Bot token | Experimental | [Telegram Bot API](https://core.telegram.org/bots/api) | [telegram_bot.py](../../communication/telegram_bot.py) |
| `operator_api` | 0.1.0 | FastAPI | `/operator/command`, `/operator/upload` | Authorization header | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `open_web_ui` | 0.1.0 | Open WebUI | `/glm-command` | Bearer token | Experimental | [Open Web UI Guide](../open_web_ui.md) | [docker-compose.openwebui.yml](../../docker-compose.openwebui.yml) |
| `future` | TBD | TBD | TBD | TBD | Planned | TBD | TBD |
