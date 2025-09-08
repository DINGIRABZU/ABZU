# Chakra Heartbeat

The heartbeat layer provides the timing spine for the ABZU architecture. Every chakra emits periodic pulses consumed by monitoring components, logged for audit, and used to trigger self-healing workflows when a layer stalls. This subsystem follows the governance defined in [The Absolute Protocol](The_Absolute_Protocol.md) and fits within the architectural views of the [Blueprint Spine](blueprint_spine.md) and [System Blueprint](system_blueprint.md). New contributors should complete the [Onboarding Checklist](onboarding/README.md) before modifying heartbeat logic.

## Function

### `ChakraHeartbeat`
Tracks the last heartbeat per chakra, persists timestamps through an optional Redis store, and exports Prometheus metrics (`chakra_heartbeats_total`, `chakra_last_heartbeat_timestamp`). It can raise `chakra_down` or `great_spiral` events based on synchronization state.

*Source: [`monitoring/chakra_heartbeat.py`](../monitoring/chakra_heartbeat.py)*

### `AgentHeartbeat`
Maintains last-seen timestamps for agents and raises runtime errors when agents fall silent beyond a configurable window.

*Source: [`monitoring/agent_heartbeat.py`](../monitoring/agent_heartbeat.py)*

### Watchdogs
[`monitoring/chakra_watchdog.py`](../monitoring/chakra_watchdog.py) and [`monitoring/avatar_watchdog.py`](../monitoring/avatar_watchdog.py) poll heartbeat maps and emit events when delays exceed thresholds.

### Logging & Persistence
[`monitoring/heartbeat_logger.py`](../monitoring/heartbeat_logger.py) writes JSONL entries for each cycle, while [`monitoring/self_healing_ledger.py`](../monitoring/self_healing_ledger.py) captures recovery steps and maintains durable heartbeat state.

### Endpoints & Dashboards
[`monitoring/chakra_status_board.py`](../monitoring/chakra_status_board.py), [`monitoring/chakra_status_endpoint.py`](../monitoring/chakra_status_endpoint.py), and [`monitoring/agent_status_endpoint.py`](../monitoring/agent_status_endpoint.py) expose heartbeat frequencies and versions for observability dashboards or the web console.

Together, these pieces ensure consistent timing, early detection of failures, and a data trail for post‑mortem analysis.

## Meaning
The heartbeat subsystem acts as the platform's temporal coordinator:

- Defines a canonical clock shared by all layers.
- Couples service health with event synchronization—missed beats directly signal an outage.
- Powers automated recovery: heartbeat discrepancies trigger self-healing routines and influence the boot orchestrator's start-up decisions ([`agents/razar/boot_orchestrator.py`](../agents/razar/boot_orchestrator.py)).

## Reach
Heartbeat signals propagate through multiple surfaces:

- **Internal connectors**: Discord, Telegram, and avatar broadcast components mirror chakra and cycle counts when relaying data.
- **Monitoring stack**: Prometheus metrics, FastAPI status endpoints, and web dashboards consume heartbeat data for real-time status and alerts.
- **Operations workflows**: Boot orchestration, event logs, and self-healing ledgers depend on accurate heartbeat telemetry.

This cross-cutting concern keeps the stack coherent from runtime agents up to operator-facing dashboards.

## Current State
- Stable per-chakra and per-agent heartbeat tracking with pluggable persistence.
- Watchdog loops detect delays but are single-instance; clustering is manual.
- Metrics and logging cover core flows; tests exist for status endpoints (`tests/monitoring/test_chakra_status_board.py`) but global coverage remains below the repository’s threshold.
- Regression tests ensure a component relaunches after an Opencode patch and logs the attempt, tying fault recovery into the heartbeat model.

## Vision for future iterations
1. **Cluster-aware heartbeat consensus** – implement distributed election and quorum checks so heartbeat consensus holds across multi-node deployments.
2. **Adaptive thresholds & anomaly detection** – use historical beat variance to auto-tune watchdog delay thresholds and surface predictive alerts.
3. **Unified recovery orchestration** – integrate heartbeat analysis with `_retry_with_ai` and the self-healing ledger to automatically patch, restart, and document recoveries without operator intervention.
4. **Fine-grained telemetry** – expand metrics to include heartbeat jitter and per-connector propagation delays; expose them via the status endpoints.
5. **Developer toolchain integration** – provide local simulators and CI hooks to emulate heartbeat storms, ensuring connectors conform to heartbeat propagation contracts before deployment.
