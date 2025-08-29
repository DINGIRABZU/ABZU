# Connector Index

For shared patterns across connectors see the [Connector Overview](README.md).

| Name | Version | Endpoint | Auth Method | Status | Links |
| --- | --- | --- | --- | --- | --- |
| WebRTC Connector | 0.2.0 | `POST /call` | JWT | Experimental | [Docs](../communication_interfaces.md) / [Code](../../connectors/webrtc_connector.py) |
| Telegram Bot | 0.1.0 | Telegram API (polling) | Bot token | Experimental | [Docs](../communication_interfaces.md) / [Code](../../communication/telegram_bot.py) |
| Operator API | 0.0.0 | `/operator/command`, `/operator/upload` | Authorization header | Experimental | [Docs](../operator_protocol.md) / [Code](../../operator_api.py) |
| Open Web UI | 0.1.0 | `/glm-command` | GLM command token | Experimental | [Docs](../open_web_ui.md) / [Code](../../server.py) |
| Future Connectors | TBD | TBD | TBD | Planned | [Docs](README.md) / - |

