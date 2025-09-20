# RAZAR Failover Monitoring

The RAZAR orchestrator exports detailed telemetry about AI handovers, retry
loops, and cross-agent escalations. Prometheus scrapes these metrics from the
`scripts/razar.metrics` endpoint while Grafana visualizes the data through the
`monitoring/grafana/razar_failover.json` dashboard. This guide outlines the
required setup and the alert thresholds that backstop the failover ladder.

## Setup Steps

1. **Enable metrics export.** Call `razar.metrics.init_metrics()` during service
   startup (or launch `python -m razar.metrics`) so Prometheus can scrape the
   counters and histograms on port `9360`. The exporter respects the
   `RAZAR_METRICS_PORT` environment variable when the default port conflicts
   with an existing service.
2. **Expose the metrics endpoint.** Add the target to
   `monitoring/prometheus.yml` so Prometheus scrapes both the handover
   histograms and the Crown readiness gauge:
   ```yaml
   - job_name: 'razar-metrics'
     static_configs:
       - targets: ['razar-metrics:9360']
         labels:
           chakra: crown
   ```
   Restart Prometheus (or run `docker compose up prometheus` inside
   `monitoring/`) so the new job is loaded. The same scrape delivers the
   `crown_identity_ready` gauge emitted by `init_crown_agent`, keeping the
   failover dashboard aware of Crown boot status.
3. **Import the Grafana dashboard.** Upload
   `monitoring/grafana/razar_failover.json` via the Grafana UI or by copying the
   file into `/var/lib/grafana/dashboards/`. The dashboard automatically
   populates `component` and `agent` template variables using Prometheus
   metadata.
4. **Load alert rules.** Reference
   `monitoring/alerts/razar_failover.yml` from the Prometheus alertmanager
   configuration. When running the bundled docker-compose stack, mount the file
   and restart the Prometheus container to activate the rules.
5. **Verify the schema.** Execute `python scripts/ci_verify_dashboards.py` in CI
   and locally to ensure dashboards remain well-formed before deploying.

## Nightly Telemetry Ledger

Nightly automation should call `python scripts/ingest_razar_telemetry.py` to
condense the JSON lines in `logs/razar_ai_invocations.json`. The job produces two
artifacts under `monitoring/self_healing_ledger/`:

- `razar_agent_trends.json` – ISO-8601 keyed summaries per agent/component/day
  used by Grafana for quick comparisons.
- `razar_agent_trends.parquet` – schema-stable table for analytics notebooks and
  longer retention in warehouse jobs.

The ingest routine tolerates malformed rows and ignores entries missing
timestamps or status flags so nightly runs keep flowing even when a delegation
emits partial telemetry. Override defaults with
`python scripts/ingest_razar_telemetry.py --log-path <custom> --output-dir <dir>`
if replaying history inside a sandbox.

Grafana reads the JSON snapshot via the
`yesoreyeram-infinity-datasource` plugin. Point a data source at
`/monitoring/self_healing_ledger/razar_agent_trends.json` (or the hosted
equivalent) and select it from the new `Self-Healing Ledger` dashboard variable
before loading the panels described below.

## Dashboard Panels

The dashboard surfaces the following signals:

- **Retry Attempts by Component** – stacked timeseries derived from
  `razar_ai_invocation_retries_total` to show which component is consuming
  retries per scrape window.
- **Agent Success Rate** – percentage of successful handovers per component
  calculated from `razar_ai_invocation_success_total` and
  `razar_ai_invocation_failure_total`. Components falling below the 75% threshold
  should trigger investigation.
- **Retry Loop Duration (sum)** – cumulative seconds spent in the retry loop via
  `razar_ai_retry_duration_seconds_sum`, highlighting components that are
  approaching escalation.
- **Retry Loop Iterations** – derivative of
  `razar_ai_invocation_retries_total` to reveal how quickly retries are accruing
  for each component.
- **External Agent Latency** – moving average of
  `razar_agent_call_duration_seconds` to track downstream agent responsiveness.
- **Escalation Loop Warning** – stat panel that surfaces the largest retry-loop
  duration in the last 30 minutes so operators can intervene before the loop
  saturates.
- **Crown Identity Ready** – single-stat panel pinned to the dashboard header
  showing the `crown_identity_ready` gauge. Keep the thresholds at green `1`
  and red `0`; collapse the panel when operating outside of Crown contexts.
- **Ledger Agent Success Trend** – table sourced from the nightly ledger that
  lists attempts, success counts, and failure totals per agent/component/day.
- **Ledger Lowest Success Rate** – stat highlight fed by the ledger JSON that
  surfaces the weakest success rate so the architect can triage targeted
  escalations.

Stage B readiness reviews now require the accompanying memory initialization
gauges exported by the boot scripts. The `monitoring/boot_metrics.prom` textfile
exposes per-source readings for `razar_memory_init_duration_seconds`, layer
totals (`razar_memory_init_layer_total`, `…_ready_total`, `…_failed_total`), the
binary failure flag (`razar_memory_init_error`), and the cumulative invocation
count (`razar_memory_init_invocations_total`). Pair these gauges with the log
fields `memory_layers`, `memory_init_duration`, `memory_init_ready`, and
`memory_init_failed` emitted by `razar.boot_orchestrator`,
`scripts/bootstrap_memory.py`, and `scripts/bootstrap_world.py` when proving a
10 k-item audit to operations.

### Memory load proof telemetry

Operators attach a dedicated load proof to Stage B packages using
`python scripts/memory_load_proof.py <fixture>`. The CLI writes latency
percentiles (P50/P95/P99) and the replayed record counts to
`logs/memory_load_proof.jsonl`, while `record_memory_init_metrics` refreshes the
`razar_memory_init_*` gauges under the supplied `--metrics-source` label.

1. Produce (or request) a 10 k-record JSONL fixture where each line contains a
   `query` field. Store it alongside prior audits under
   `data/memory/load_proofs/`.
2. Run the CLI with Stage B labels. Example:

   ```bash
   python scripts/memory_load_proof.py data/memory/load_proofs/stageb_fixture.jsonl \
     --metrics-source stageb-readiness --warmup 25
   ```

3. Export `monitoring/boot_metrics.prom` and the appended JSON log for review.

**Acceptance thresholds** for the audit remain `p95 ≤ 0.120 s` and
`p99 ≤ 0.180 s`. Any non-ready layers or replay failures must be documented in the
operations log with remediation notes before sign-off.

### Navigation Notes for the New Architect

1. From the Grafana home page, open **Dashboards → RAZAR Failover Observability**.
2. Choose the failing component/agent combo from the Prometheus-powered
   variables at the top of the screen.
3. Switch the **Self-Healing Ledger** variable to the Infinity data source that
   points at `monitoring/self_healing_ledger/razar_agent_trends.json`.
4. Inspect **Ledger Agent Success Trend** for the last day of results—rows are
   sorted by newest date so the freshest handovers appear first.
5. Use **Ledger Lowest Success Rate** to decide whether manual escalation is
   needed before the retry loop saturates.

## Alert Thresholds

| Alert | Expression | Threshold | Recommended Action |
| --- | --- | --- | --- |
| `RAZARExcessiveRetries` | `sum(increase(razar_ai_invocation_retries_total[5m])) by (component) > 10` | More than 10 retries in 5 minutes | Check the component log, confirm self-healing succeeds, and reseed mission context if necessary. |
| `RAZARAgentSuccessRateLow` | Success rate below `0.75` for 10 minutes | Success rate < 75% | Validate external agent credentials, ensure upstream APIs are reachable, and review the [RAZAR Escalation Runbook](../runbooks/razar_escalation.md). |
| `RAZAREscalationLoopStalled` | `sum(increase(razar_ai_retry_duration_seconds_sum[30m])) by (component) > 900` | >15 minutes spent inside the retry loop | Trigger operator escalation per the runbook and inspect `logs/operator_escalations.jsonl` for stuck events. |
| `CrownIdentityUnavailable` | `min_over_time(crown_identity_ready[5m]) < 1` | Gauge drops to 0 for 5 minutes | Page the architect to reseat doctrine files, rerun `init_crown_agent`, and confirm the fingerprint JSON under `crown/state/`. |

When alerts fire, document the outcome in `logs/operator_escalations.jsonl` so
future cycles inherit context.

## Runbooks and References

- [RAZAR Escalation Runbook](../runbooks/razar_escalation.md)
- [Co-creation Escalation Protocol](../co_creation_escalation.md)
- [Monitoring Guide](../monitoring.md)

## Automation and Validation

CI executes `scripts/ci_verify_dashboards.py` to confirm that the Grafana
JSON stays consistent with the expected schema. Run the script locally after
editing dashboards or alert rules to catch formatting issues before committing.

### Doctrine References
- [system_blueprint.md#configurable-crown-escalation-chain](../system_blueprint.md#configurable-crown-escalation-chain)
- [runbooks/razar_escalation.md](../runbooks/razar_escalation.md)
