# Connector Index

For shared patterns across connectors see the [Connector Overview](README.md).

| id | version | purpose | service | endpoints | auth | status | docs | code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `webrtc` | 0.2.0 | Streams avatar audio/video | WebRTC | `POST /call` | JWT | Experimental | [Nazarick Web Console](../nazarick_web_console.md) | [webrtc_connector.py](../../connectors/webrtc_connector.py) |
| `telegram_bot` | 0.1.0 | Chat bridge for Telegram users | Telegram Bot API | Telegram API (polling) | Bot token | Experimental | [Telegram Bot API](https://core.telegram.org/bots/api) | [telegram_bot.py](../../communication/telegram_bot.py) |
| `operator_api` | 0.1.0 | Operator commands and uploads | FastAPI | `/operator/command`, `/operator/upload` | Authorization header | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `open_web_ui` | 0.1.0 | Self-hosted multi-user chat | Open WebUI | `/glm-command` | Bearer token | Experimental | [Open Web UI Guide](../open_web_ui.md) | [docker-compose.openwebui.yml](../../docker-compose.openwebui.yml) |
| `future` | TBD | TBD | TBD | TBD | TBD | Planned | TBD | TBD |
