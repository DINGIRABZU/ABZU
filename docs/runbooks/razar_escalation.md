# RAZAR Escalation Runbook

RAZAR escalates stubborn component failures through a remote ladder when on-host
self-healing loops cannot restore service. This runbook summarizes the controls,
telemetry, and operator actions required to shepherd an incident from first
alert through rStar intervention.

## Escalation Ladder and Threshold Controls

- **Default ordering:** Crown → Kimi-cho → [Kimi 2 (K2 Coder)](https://github.com/MoonshotAI/Kimi-K2)
  → [rStar](https://github.com/microsoft/rStar). The sequence is stored in
  [`config/razar_ai_agents.json`](../../config/razar_ai_agents.json). Confirm the
  roster before changing thresholds so the warning and escalation counts line up
  with actual agents.
- **`RAZAR_ESCALATION_WARNING_THRESHOLD`** – emits operator warnings after the
  specified number of escalations during a boot or repair cycle. Leave it ≥1 so
  alerts fire before rStar receives traffic.
- **`RAZAR_RSTAR_THRESHOLD`** – cumulative attempts (across all agents) before
  rStar takes over. The default `9` gives three full passes through the local
  stack. Setting it to `0` disables rStar entirely.
- **`RSTAR_ENDPOINT` / `RSTAR_TOKEN`** – API target and credential for rStar.
  Pair them with `KIMI_K2_URL` and `KIMI_K2_TOKEN` (if present) so K2 Coder can
  authenticate during its turn in the ladder.
- **`RAZAR_METRICS_PORT`** – port for Prometheus counters that track invocation
  volume, failures, and retries. Defaults to `9360`.

After tuning the environment variables, restart the orchestrator so the new
values propagate into the escalation registry and metrics exporter.

## Context and Log Triage

RAZAR automatically shares escalation history with downstream agents via
`build_failure_context` (`razar/boot_orchestrator.py`). Each retry loads the
latest entries from `logs/razar_ai_invocations.json` and forwards them as the
`context` payload to `ai_invoker.handover`, ensuring K2 Coder and rStar see every
previous failure, patch attempt, and rejection.

Operators should triage incidents with the following artifacts:

```bash
# Recent orchestration state changes and component failures
tail -n 50 logs/razar.log

# Escalation history (JSON lines). Filter by component with jq when available.
tail -n 50 logs/razar_ai_invocations.json
jq 'select(.component=="crown_router")' logs/razar_ai_invocations.json

# Applied patches and rollbacks
tail -n 20 logs/razar_ai_patches.json
tail -n 20 logs/patch_history.jsonl
```

Review `logs/razar_state.json` for mission-level health and quarantine status.
If the same component triggers repeated escalations, capture the relevant JSON
lines and attach them to the incident ticket so downstream agents inherit the
full trail.

## Metrics and Dashboards

Prometheus counters expose escalation health alongside the structured logs:

```bash
# Invocation counters served by razar.metrics (defaults to port 9360)
curl -s http://localhost:9360/metrics | grep razar_ai_invocation

# Chakra heartbeat metrics published by the monitoring service
curl -s http://localhost:8000/metrics | head
```

The RAZAR exporter surfaces `razar_ai_invocation_failure_total`,
`razar_ai_invocation_success_total`, and `razar_ai_invocation_retries_total`
per component. A sudden spike in failures for the same component indicates the
thresholds are about to trip. Pair these counters with the chakra heartbeat
metrics (`chakra_pulse_hz`, `chakra_alignment`) to confirm whether the incident
is isolated or affecting multiple layers.

Run `python scripts/verify_chakra_monitoring.py` when diagnosing a prolonged
outage; it probes the `/metrics` endpoints (node exporter, cAdvisor, GPU
exporter) and reports gaps in the monitoring fabric.

## Rollback and Recovery Actions

1. **Stop the destabilized component** with the operator console or via the
   lifecycle bus: `python -m razar stop <component>`.
2. **Rollback recent patches** with the documented helper:

   ```bash
   python scripts/rollback_patch.py <component>
   ```

   The script restores the previous artifact, appends a `reverted` record to
   `logs/patch_history.jsonl`, and updates the boot snapshot.
3. **Re-run the handover flow** once the component is stable:

   ```bash
   python -m razar.boot_orchestrator --config razar/boot_config.json --long-task \
     --retries 0 --remote-attempts 1
   ```

   The `--long-task` flag keeps the orchestrator in escalation mode until the
   remote service returns success or the operator aborts, ensuring rStar receives
   the refreshed context if earlier agents still cannot patch the issue.
4. **Document the timeline** – capture the warning threshold, invocation counts,
   log excerpts, and metrics snapshots before closing the incident.

## External Service References

- [Kimi 2 (K2 Coder)](https://github.com/MoonshotAI/Kimi-K2) – remote repair
  engine invoked after Kimi-cho.
- [rStar](https://github.com/microsoft/rStar) – final escalation target for
  high-assurance patch generation.

Keep the upstream documentation handy when debugging remote API changes or
credential rotations.
