# Crown Agent Overview

The diagram below shows how the main components interact when using the console.

```
+--------------------+
|    Crown Console   |
+---------+----------+
          |
          v
+---------+----------+
|   Crown Agent      |
| (GLMIntegration)   |
+---------+----------+
          |
          v
+---------+----------+
| State Transition   |
| Engine             |
+---------+----------+
          |
     +----+----+
     |         |
     v         v
+--------+ +---------------+
|  GLM   | | Servant Models|
| 4.1V   | | (DeepSeek etc)|
+--------+ +---------------+
```

User commands enter through the **Crown Console**. The **Crown Agent** sends
requests to the GLM service and keeps recent history in memory. The
**State Transition Engine** tracks ritual phrases and emotional cues. It may
delegate a prompt to one of the registered servant models when appropriate.

## Memory‑Aided Routing

The Crown router looks up previous expression decisions in `vector_memory`. When the stored `soul_state` aligns with the current emotion, the corresponding voice backend and avatar style are weighted higher. This memory‑aided approach keeps responses consistent with past interactions.

## Session Logger

Running the console interface now writes audio clips under `logs/audio/` and avatar frames to `logs/video/`. These helpers live in `tools/session_logger.py` and make it easier to review how voice modulation and streaming evolve across sessions.

## Automated Module Repair

The Crown stack can defer failing components to the RAZAR agent for automatic
patching. See [RAZAR Agent](RAZAR_AGENT.md) for details on the repair workflow
that queries an LLM for fixes and reintroduces modules after successful tests.

## Crown Link Protocol

RAZAR communicates with the Crown stack over a small WebSocket interface
implemented in `razar/crown_link.py`. Two JSON message types are exchanged:

- **Status updates** – `{"type": "status", "component": "state_engine", "result": "ok", "log_snippet": "..."}`
- **Repair requests** – `{"type": "repair", "stack_trace": "...", "config_summary": "..."}`

The Crown side replies with patch instructions which RAZAR uses to heal faulty
modules before reintroducing them into the boot cycle. See the
[RAZAR Agent](RAZAR_AGENT.md#crown-link-protocol) document for detailed schema
descriptions.

## Mission Brief Handshake

Before diagnostics begin, RAZAR shares a short mission brief with the Crown stack. The brief summarises the priority map, current status and any open issues and is sent via the WebSocket helper `razar/crown_handshake.py`. Crown replies with an acknowledgment and a capability list so RAZAR knows which tools are available for the session. Each exchange is recorded to `logs/razar_crown_dialogues.json` for later review.

## Deployment

1. Configure the environment with [`init_crown_agent.py`](../init_crown_agent.py). This script prepares memory directories, registers servant models, and validates the GLM endpoint.
2. Exchange a mission brief using [`razar/crown_handshake.py`](../razar/crown_handshake.py) so RAZAR and the Crown stack agree on available capabilities before entering the boot cycle.
3. Launch the console to begin a session after the handshake completes.

## Version History

| Version | Date       | Summary |
|---------|------------|---------|
| 0.2.0   | 2025-09-30 | Added deployment guidance and initial version table. |
| 0.1.0   | 2025-08-28 | Initial document outlining Crown agent architecture. |
