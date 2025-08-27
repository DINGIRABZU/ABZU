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
modules before reintroducing them into the boot cycle.
