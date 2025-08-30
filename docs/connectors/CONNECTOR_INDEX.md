# Connector Index

Canonical registry of ABZU's connectors. Each entry lists the purpose, version,
primary service endpoints, authentication method, current status, and
references to documentation and source code. Update this index whenever a
connector's interface changes. For shared patterns across connectors see the
[Connector Overview](README.md).

| id | purpose | version | endpoints | auth | status | docs | code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `webrtc` | real-time avatar streaming bridge | 0.2.0 | `POST /call` | JWT | Experimental | [Nazarick Web Console](../nazarick_web_console.md) | [webrtc_connector.py](../../connectors/webrtc_connector.py) |
| `operator_api` | operator command and upload interface | 0.1.0 | `/operator/command`, `/operator/upload` | Authorization header | Experimental | [Operator Protocol](../operator_protocol.md) | [operator_api.py](../../operator_api.py) |
| `open_web_ui` | bridge to Open WebUI for GLM commands | 0.1.0 | `/glm-command` | Bearer token | Experimental | [Open Web UI Guide](../open_web_ui.md) | [docker-compose.openwebui.yml](../../docker-compose.openwebui.yml) |
| `telegram_bot` | Telegram bot integration | 0.1.0 | Telegram API (polling) | Bot token | Experimental | [Telegram Bot API](https://core.telegram.org/bots/api) | [telegram_bot.py](../../communication/telegram_bot.py) |
