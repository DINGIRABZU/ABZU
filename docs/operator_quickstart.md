# Operator Quickstart

A concise orientation for operators interacting with ABZU.

## Triple-Reading Rule
Before issuing commands or editing code, read [blueprint_spine.md](blueprint_spine.md) three times as mandated by the [The Absolute Protocol](The_Absolute_Protocol.md). The repetition ensures the project's structure and intent are internalized.

## Consent Logging
Record explicit consent for every session. Log the operator, participants, timestamp, and scope in the canonical ledger so actions remain auditable and reversible. Reference the ethical laws in the [nazarick_manifesto.md](nazarick_manifesto.md) when verifying that consent covers all planned interactions.

## Avatar Console Setup

1. **Configure** – edit [`guides/avatar_config.toml`](../guides/avatar_config.toml) to select textures and colors described in [avatar_pipeline.md](avatar_pipeline.md).
2. **Launch** – start the avatar console and WebRTC stream:
   ```bash
   bash start_avatar_console.sh
   ```
3. **Connect** – with tokens in `secrets.env`, run external channels:
   ```bash
   python communication/webrtc_server.py
   python tools/bot_discord.py
   python tools/bot_telegram.py
   ```
   See [communication_interfaces.md](communication_interfaces.md) for connector behaviour and authentication.
