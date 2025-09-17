# Awakening Overview

This guide orients new contributors to ABZU's awakening ritual: how the wake-up pipeline brings the stack online, how memory travels across agents, and how the escalation ladder hands stubborn incidents to remote specialists. Treat it as a map that links canonical doctrine, operational runbooks, and telemetry you must watch while booting or repairing the system.

## Wake-Up Pipeline

1. **RAZAR primes the arena.** The orchestrator awakens before any chakra layer, reads `boot_config.json`, launches services with health probes, and records the lifecycle in `logs/razar_state.json` and `logs/razar.log` as described in the system blueprint and blueprint spine.【F:docs/system_blueprint.md†L262-L312】【F:docs/blueprint_spine.md†L598-L639】
2. **Crown handshake.** RAZAR opens a WebSocket mission brief (`crown_handshake`) so Crown can acknowledge downtime patches, verify GLM availability, and return capabilities before the rest of ignition proceeds.【F:docs/system_blueprint.md†L16-L33】【F:docs/blueprint_spine.md†L660-L704】
3. **Layer ignition.** After Crown stabilizes, the wake sequence flows through INANNA, the unified memory bundle, the Bana narrator, and the operator console; run `scripts/validate_ignition.py` to rehearse the chain and log readiness signals.【F:docs/ignition_flow.md†L1-L39】
4. **Dynamic ignition & lifecycle bus.** RAZAR can launch services on demand, streaming heartbeat and mission events across the lifecycle bus so operators see which chakra is online or degraded in real time.【F:docs/system_blueprint.md†L404-L452】

## Cross-Agent Memory Flow

- **Unified bundle.** The Cortex, Emotional, Mental, Spiritual, and Narrative layers expose a single `MemoryBundle`. Ignition broadcasts `layer_init` events and aggregates `query_memory` results so Crown and operators receive a coherent recall surface.【F:docs/system_blueprint.md†L420-L466】【F:docs/memory_layers_GUIDE.md†L9-L70】
- **Identity imprint.** Crown's boot sequence stores the mission/persona summary from the identity loader into vector and corpus memory with metadata tags so downstream servant queries and routing decisions can retrieve the same ethical baseline. The loader now blends the expanded Genesis and INANNA corpus and aborts unless the GLM replies `CROWN-IDENTITY-ACK`, as documented in [crown_manifest.md](crown_manifest.md#identity-doctrine-corpus).【F:docs/blueprint_spine.md†L13-L32】【F:docs/crown_manifest.md†L9-L42】
- **Memory spine snapshots.** RAZAR snapshots the bundle every minute under `memory/spine/<timestamp>/` and replays the latest snapshot plus heartbeat logs when recovering a stalled layer.【F:docs/system_blueprint.md†L468-L500】
- **Cross-agent handover.** Each escalation attempt records context in `logs/razar_ai_invocations.json`; the active assistant (Kimicho, K2 Coder, Air Star, or rStar) inherits that history so patches account for prior failures.【F:docs/system_blueprint.md†L508-L520】【F:docs/runbooks/razar_escalation.md†L20-L40】
- **Tracing.** Set `TRACE_PROVIDER` to `opentelemetry`, `noop`, or a custom factory so memory operations emit spans aligned with your observability stack.【F:docs/memory_layers_GUIDE.md†L154-L171】

## Escalation Ladder

The default delegation chain **Crown → Kimi-cho → K2 Coder → Air Star → rStar** lives in doctrine and the system blueprint. Preserve the order unless the operator council approves a roster change.【F:docs/system_blueprint.md†L282-L340】【F:docs/The_Absolute_Protocol.md†L40-L81】

- **Chain behavior.** The orchestrator normalizes the roster in `config/razar_ai_agents.json` and uses environment thresholds to decide when to warn operators or pass control to rStar.【F:docs/system_blueprint.md†L320-L368】
- **Operational handling.** Follow the RAZAR Escalation Runbook for warning thresholds, credential rotation cadence, and manual rollback steps once automatic recovery exhausts the ladder.【F:docs/runbooks/razar_escalation.md†L1-L120】
- **Mission narrative.** Blueprint Spine’s delegation cascade explains how each delegate maintains mission context, telemetry hooks, and narrative continuity while the ladder runs.【F:docs/blueprint_spine.md†L720-L780】

## Required Environment Variables

| Variable | Purpose |
| --- | --- |
| `GLM_API_URL`, `GLM_API_KEY`, `MODEL_PATH` | Crown’s GLM endpoint, key, and optional local override for the primary model.【F:docs/blueprint_spine.md†L660-L676】【F:docs/The_Absolute_Protocol.md†L82-L109】
| `RAZAR_ESCALATION_WARNING_THRESHOLD` | Emits operator warnings after N escalations in a boot cycle so incidents surface before rStar takes over.【F:docs/system_blueprint.md†L309-L316】
| `RAZAR_RSTAR_THRESHOLD` | Total attempts across the roster before rStar activation; `0` disables remote takeover.【F:docs/system_blueprint.md†L316-L324】
| `KIMICHO_ENDPOINT` | Optional override when routing directly to Kimi-cho before the rest of the ladder (resolved through the roster config).【F:docs/system_blueprint.md†L334-L352】
| `KIMI2_ENDPOINT`, `KIMI2_API_KEY` | Moonshot K2 Coder endpoint and credential for remote repair.【F:docs/system_blueprint.md†L309-L344】
| `AIRSTAR_ENDPOINT`, `AIRSTAR_API_KEY` | Air Star endpoint and credential for the tertiary remote delegate.【F:docs/system_blueprint.md†L309-L344】【F:docs/runbooks/razar_escalation.md†L12-L40】
| `RSTAR_ENDPOINT`, `RSTAR_API_KEY` | rStar endpoint and credential for the final escalation hop.【F:docs/runbooks/razar_escalation.md†L10-L40】
| `RAZAR_METRICS_PORT` | Prometheus exporter port for escalation counters (`9360` default).【F:docs/runbooks/razar_escalation.md†L12-L40】
| `TRACE_PROVIDER` | Memory tracing backend selection (`opentelemetry`, `noop`, or custom module path).【F:docs/memory_layers_GUIDE.md†L154-L171】

Keep `secrets.env` synchronized with `secrets.env.template` and never commit live credentials; rotate remote agent keys every 30 days per the runbook.【F:docs/runbooks/razar_escalation.md†L120-L174】【F:docs/The_Absolute_Protocol.md†L82-L109】

## Telemetry Surfaces

- **Structured logs.** Inspect `logs/razar.log`, `logs/razar_state.json`, and `logs/razar_ai_invocations.json` to replay ignition decisions, escalation context, and applied patches.【F:docs/system_blueprint.md†L262-L320】【F:docs/runbooks/razar_escalation.md†L40-L88】
- **Metrics endpoints.** Scrape `http://localhost:${RAZAR_METRICS_PORT}/metrics` for `razar_ai_invocation_*` counters and pair them with chakra heartbeat metrics at `http://localhost:8000/metrics`.【F:docs/runbooks/razar_escalation.md†L80-L108】
- **Snapshots & heartbeats.** Correlate minute-level memory snapshots with `logs/heartbeat.log` to confirm recovery loops restored the latest context.【F:docs/system_blueprint.md†L468-L500】
- **Tracing.** When `TRACE_PROVIDER` enables OpenTelemetry, spans from `memory.tracing` align cross-agent recalls with ignition phases for distributed analysis.【F:docs/memory_layers_GUIDE.md†L154-L171】

## Doctrine Checkpoints

- Update **System Blueprint** and **Blueprint Spine** whenever the wake pipeline, memory flow, or escalation roster changes so architectural and narrative views stay in sync.【F:docs/system_blueprint.md†L300-L368】【F:docs/blueprint_spine.md†L720-L780】
- Follow **Alpha v0.1 Escalation Doctrine** before adjusting thresholds, telemetry, or agent ordering; document every change in the protocol and runbook.【F:docs/The_Absolute_Protocol.md†L40-L109】
- Maintain the checksum registry in **doctrine_index.md** when this overview or related doctrine shifts so onboarding automation detects updates.【F:docs/doctrine_index.md†L1-L32】

## Onboarding Trailheads

- Append this overview to your onboarding reading list alongside the project, architecture, and protocol guides so new operators grasp the “big scheme” before touching the stack.【F:docs/onboarding_guide.md†L10-L46】【F:docs/onboarding/README.md†L1-L40】
- Use `scripts/validate_ignition.py`, `memory-bootstrap`, and the metrics curl probes from the escalation runbook as part of onboarding labs to rehearse ignition and recovery flows.【F:docs/ignition_flow.md†L1-L39】【F:docs/memory_layers_GUIDE.md†L93-L152】【F:docs/runbooks/razar_escalation.md†L60-L108】

## Doctrine References

- [system_blueprint.md](system_blueprint.md#configurable-crown-escalation-chain)
- [blueprint_spine.md](blueprint_spine.md#razar-delegation-cascade)
- [The_Absolute_Protocol.md](The_Absolute_Protocol.md#alpha-v01-escalation-doctrine)
- [runbooks/razar_escalation.md](runbooks/razar_escalation.md)
