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
   `monitoring/prometheus.yml`:
   ```yaml
   - job_name: 'razar-metrics'
     static_configs:
       - targets: ['razar-metrics:9360']
         labels:
           chakra: crown
   ```
   Restart Prometheus (or run `docker compose up prometheus` inside
   `monitoring/`) so the new job is loaded.
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

## Alert Thresholds

| Alert | Expression | Threshold | Recommended Action |
| --- | --- | --- | --- |
| `RAZARExcessiveRetries` | `sum(increase(razar_ai_invocation_retries_total[5m])) by (component) > 10` | More than 10 retries in 5 minutes | Check the component log, confirm self-healing succeeds, and reseed mission context if necessary. |
| `RAZARAgentSuccessRateLow` | Success rate below `0.75` for 10 minutes | Success rate < 75% | Validate external agent credentials, ensure upstream APIs are reachable, and review the [RAZAR Escalation Runbook](../runbooks/razar_escalation.md). |
| `RAZAREscalationLoopStalled` | `sum(increase(razar_ai_retry_duration_seconds_sum[30m])) by (component) > 900` | >15 minutes spent inside the retry loop | Trigger operator escalation per the runbook and inspect `logs/operator_escalations.jsonl` for stuck events. |

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
