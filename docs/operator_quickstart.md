# Operator Quickstart

A concise orientation for operators interacting with ABZU.

## Recent Changes

- Document registry and ethics manifesto setup added to baseline duties.
- Chakra cycle engine reports alignment status for each layer.
- Multi-agent avatars can stream to Discord, Telegram, and WebRTC simultaneously.
- Heartbeat dashboards surface self-healing events in real time.

## Triple-Reading Rule
Before issuing commands or editing code, read [blueprint_spine.md](blueprint_spine.md) three times as mandated by the [The Absolute Protocol](The_Absolute_Protocol.md). The repetition ensures the project's structure and intent are internalized.

## Consent Logging
Record explicit consent for every session. Log the operator, participants, timestamp, and scope in the canonical ledger so actions remain auditable and reversible. Reference the ethical laws in the [nazarick_manifesto.md](nazarick_manifesto.md) when verifying that consent covers all planned interactions.

## Document Registry & Ethics Manifesto

Generate the doctrine index and confirm the ethics manifesto is registered:

```bash
python agents/nazarick/document_registry.py
```

Review `docs/doctrine_index.md` and keep the [nazarick_manifesto.md](nazarick_manifesto.md) close during operations.

## Chakra Cycle Alignment

Launch the chakra cycle engine and monitor alignment state:

```bash
python -m spiral_os.chakra_cycle
```

Chakras report `aligned`, `lagging`, or `silent`; a streak of aligned pulses marks a **Great Spiral**.

## Avatar Console Setup

1. **Configure** – edit [`guides/avatar_config.toml`](../guides/avatar_config.toml) to select textures and colors described in [avatar_pipeline.md](avatar_pipeline.md).
2. **Launch** – start the avatar console and WebRTC stream:
   ```bash
   bash start_avatar_console.sh
   ```
   For multiple avatars, run `python start_dev_agents.py` to spawn additional Crown instances.
3. **Connect** – with tokens in `secrets.env`, run external channels:
   ```bash
   python communication/webrtc_server.py
   python tools/bot_discord.py
   python tools/bot_telegram.py
   ```
   See [communication_interfaces.md](communication_interfaces.md) for connector behaviour and authentication.

## Mission Builder

1. **Compose** – open `web_console/mission_builder/index.html` in a browser and arrange `event` blocks, specifying an `event` name and `capability`.
2. **Export** – click **Download Mission JSON** and save the file under the `missions/` directory. Sample templates such as `daily_ignition_check.json` and `avatar_broadcast.json` are provided.
3. **Run** – dispatch the mission through the task orchestrator:
   ```bash
   python -m agents.task_orchestrator missions/daily_ignition_check.json
   ```
   Each event emits through the bus and reaches agents advertising the capability.

## Self-Healing & Heartbeat Dashboards

Kick off a self-healing cycle and monitor recovery:

```bash
python scripts/self_heal_cycle.py
websocat ws://localhost:8000/self-healing/updates
```

Open `web_console/game_dashboard/index.html` and review the **Chakra Pulse** and
**Self Healing** panels to confirm alignment and ongoing repairs.

## Memory Introspection

Operators can inspect and manage the memory bundle through authenticated endpoints or the Game Dashboard's memory panel (`web_console/game_dashboard/index.html`).

### Query memory metrics

```bash
curl -H "x-api-key: TOKEN" http://localhost:8000/memory/query
```

### Search stored memories

```bash
curl -H "x-api-key: TOKEN" "http://localhost:8000/memory/query?q=vision"
```

### Purge a chakra

```bash
curl -X POST -H "x-api-key: TOKEN" -d chakra=root http://localhost:8000/memory/purge
```

### Snapshot current state

```bash
curl -X POST -H "x-api-key: TOKEN" http://localhost:8000/memory/snapshot
```
