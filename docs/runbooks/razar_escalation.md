# RAZAR Escalation Runbook

RAZAR escalates stubborn component failures through a remote ladder when on-host
self-healing loops cannot restore service. This runbook summarizes the controls,
telemetry, and operator actions required to shepherd an incident from first
alert through rStar intervention.

## Escalation Ladder and Threshold Controls

- **Default ordering:** Crown → Kimi-cho → [Kimi 2 (K2 Coder)](https://github.com/MoonshotAI/Kimi-K2)
  → Air Star → [rStar](https://github.com/microsoft/rStar). The sequence is
  stored in [`config/razar_ai_agents.json`](../../config/razar_ai_agents.json).
  Confirm the roster before changing thresholds so the warning and escalation
  counts line up with actual agents.
- **`RAZAR_ESCALATION_WARNING_THRESHOLD`** – emits operator warnings after the
  specified number of escalations during a boot or repair cycle. Leave it ≥1 so
  alerts fire before rStar receives traffic.
- **`RAZAR_RSTAR_THRESHOLD`** – cumulative attempts (across all agents) before
  rStar takes over. The default `9` gives three full passes through the local
  stack. Setting it to `0` disables rStar entirely.
- **`RSTAR_ENDPOINT` / `RSTAR_API_KEY`** – API target and credential for rStar.
  Pair them with `KIMI2_ENDPOINT` / `KIMI2_API_KEY` and
  `AIRSTAR_ENDPOINT` / `AIRSTAR_API_KEY` so K2 Coder and Air Star can authenticate
  during their turns in the ladder.
- **`RAZAR_METRICS_PORT`** – port for Prometheus counters that track invocation
  volume, failures, and retries. Defaults to `9360`.

After tuning the environment variables, restart the orchestrator so the new
values propagate into the escalation registry and metrics exporter.

## Context and Log Triage

RAZAR automatically shares escalation history with downstream agents via
`build_failure_context` (`razar/boot_orchestrator.py`). Each retry loads the
latest entries from `logs/razar_ai_invocations.json` and forwards them as the
`context` payload to `ai_invoker.handover`, ensuring K2 Coder, Air Star, and
rStar see every previous failure, patch attempt, and rejection.

Operators should triage incidents with the following artifacts:

- **Crown handshake transcripts** (`logs/razar_crown_dialogues.json`). Each
  `crown` entry now appends an `identity_fingerprint` object that captures the
  SHA-256 digest and last-modified timestamp of `data/identity.json` so you can
  verify which identity summary the acknowledgement came from during
  post-incident review.

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

Stage B subsystem hardening drills also watch the new memory boot gauges
written to `monitoring/boot_metrics.prom`. Each `MemoryBundle.initialize()`
call now emits:

- `razar_memory_init_duration_seconds{source="boot_orchestrator|bootstrap_memory|bootstrap_world"}` –
  wall-clock time for the initialization pass.
- `razar_memory_init_layer_total{source="…"}` – total layers reported by the
  bundle during the attempt.
- `razar_memory_init_layer_ready_total{source="…"}` /
  `razar_memory_init_layer_failed_total{source="…"}` – ready versus failed
  layers inferred from the status strings.
- `razar_memory_init_error{source="…"}` – flag set to `1` when the run raises
  an exception or any layer reports a failure value.
- `razar_memory_init_invocations_total{source="…"}` – monotonically increasing
  counter for initialization attempts by entry point.

The orchestrator and bootstrap scripts log the same information in
`logs/razar.log` (and their console output) with the `memory_layers`,
`memory_init_duration`, `memory_init_ready`, and `memory_init_failed` fields so
auditors can confirm the textfile values without a Prometheus scrape. Capture a
copy of the log lines and the updated metrics file whenever a Stage B review
requests proof of a 10 k-item memory audit.

Run `python scripts/verify_chakra_monitoring.py` when diagnosing a prolonged
outage; it probes the `/metrics` endpoints (node exporter, cAdvisor, GPU
exporter) and reports gaps in the monitoring fabric.

## Rollback and Recovery Actions

RAZAR snapshots `config/razar_ai_agents.json` at the start of every boot cycle
and automatically restores the snapshot whenever escalations fail to heal a
component. The orchestrator emits a critical monitoring alert with the message
`Boot sequence halted; configuration rolled back to safe defaults`, writes the
event to `logs/razar.log`, and preserves the final escalation history in
`logs/razar_ai_invocations.json`. The helper lives in
`razar/boot_orchestrator.py::rollback_to_safe_defaults`, and the integration
suite (`tests/integration/test_razar_self_healing.py`) verifies both the
restoration and the recorded context.

Operators should still take the following manual steps after the automatic
rollback completes:

1. **Stop the destabilized component** with the operator console or via the
   lifecycle bus: `python -m razar stop <component>`.
2. **Rollback recent patches** with the documented helper:

   ```bash
   python scripts/rollback_patch.py <component>
   ```

   The script restores the previous artifact, appends a `reverted` record to
   `logs/patch_history.jsonl`, and updates the boot snapshot. Confirm that
   `config/razar_ai_agents.json` matches the `.bak` snapshot before proceeding.
3. **Re-run the handover flow** once the component is stable:

   ```bash
   python -m razar.boot_orchestrator --config razar/boot_config.json --long-task \
     --retries 0 --remote-attempts 1
   ```

   The `--long-task` flag keeps the orchestrator in escalation mode until the
   remote service returns success or the operator aborts, ensuring rStar receives
   the refreshed context if earlier agents still cannot patch the issue. Review
   the preserved escalation history in `logs/razar_ai_invocations.json` to brief
   downstream agents.
4. **Document the timeline** – capture the warning threshold, invocation counts,
   log excerpts (including the rollback notice), and metrics snapshots before
   closing the incident.

## Credential Rotation and Sandbox Validation

- **Cadence:** Rotate `KIMI2_API_KEY`, `AIRSTAR_API_KEY`, and `RSTAR_API_KEY`
  every 30 days or sooner when exposure, vendor notice, or operator turnover
  warrants it. The sanitized rotation manifests live under `secrets/` and map
  each agent to its environment variable and roster override.
- **Dry-run staging:** Begin every rotation with a non-destructive rehearsal so
  operators can review the generated placeholders and confirm cache invalidation
  works before touching live configuration.

  ```bash
  python scripts/rotate_remote_agent_keys.py --secrets-dir secrets --dry-run
  ```

- **Approvals:** Record a two-person approval (Security Lead + RAZAR owner) in
  the incident or change ticket before proceeding. Both approvers must confirm
  that the placeholders match the intended agents and that no emergency repair
  is currently relying on the legacy credential.
- **Sandbox apply:** With approvals captured, apply the rotation in the staging
  or sandbox environment and run the smoke checks:

  ```bash
  python scripts/rotate_remote_agent_keys.py --secrets-dir secrets --apply
  pytest tests/test_credential_rotation.py
  python -c "from razar import ai_invoker; ai_invoker.invalidate_agent_config_cache(); ai_invoker.load_agent_definitions('config/razar_ai_agents.json')"
  ```

  Export the placeholders to the sandbox service account (or inject them into
  the session with `export KIMI2_ENDPOINT=...`, `export KIMI2_API_KEY=...`,
  `export AIRSTAR_ENDPOINT=...`, `export AIRSTAR_API_KEY=...`, and equivalents)
  before executing the snippet above. The `load_agent_definitions` call must
  complete without raising `AgentCredentialError`; otherwise roll back the
  change and escalate to Security.
- **Promotion:** After sandbox validation, push the secrets manager update
  through the standard deployment pipeline, monitor the next escalation cycle,
  and attach the sandbox logs plus approval trail to the ticket before closing.

## External Service References

- [Kimi 2 (K2 Coder)](https://github.com/MoonshotAI/Kimi-K2) – remote repair
  engine invoked after Kimi-cho.
- Air Star – autonomous triage and patch refinement layer between K2 Coder and
  rStar.
- [rStar](https://github.com/microsoft/rStar) – final escalation target for
  high-assurance patch generation.

Keep the upstream documentation handy when debugging remote API changes or
credential rotations.
