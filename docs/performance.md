# Performance Profiling Report

## Overview

This report captures the recent profiling passes for the RAZAR boot
orchestrator. Instrumentation now traces both the AI retry loop and external
agent handovers so that we can measure wall-clock impact, while static
configuration loads are cached to eliminate redundant disk I/O. The goal is to
reduce mean time-to-recovery when components fail and to provide the
observability hooks needed for sustained tuning.

## Timing Instrumentation

- **Per-attempt logging.** Each call to `_retry_with_ai` records the elapsed
  time for every retry attempt, the active agent (or opencode fall back), and
  whether a patch was applied. The summary log `"AI retry loop finished"`
  captures the cumulative duration and outcome so incident responders can see
  how long recovery took without scanning multiple records.
- **Prometheus metrics.** `metrics.observe_retry_duration` feeds a new
  histogram (`razar_ai_retry_duration_seconds`) that tracks retry-loop wall
  time per component. The metric is emitted whenever the loop exits, even if no
  retry attempts were executed. This supports dashboards that highlight slow or
  repeatedly failing components.
- **Actionable context.** Each attempt log includes fields for the remote
  agent, the measured handover duration, and whether `opencode` handled the
  request. Those keys make it easy to pivot in log search tools and to
  correlate with downstream health probes.

To visualise timing data, run the boot orchestrator and query the metrics
endpoint exposed by `metrics.init_metrics()` (default `http://localhost:9360`).
Filter on `razar_ai_retry_duration_seconds` to view per-component percentiles or
per-attempt timings.

## External Agent Metrics

- **Opencode CLI and client.** Calls to the CLI now log their duration and
  populate the `razar_agent_call_duration_seconds` histogram under the
  `agent="opencode_cli"` label. When the CLI is unavailable or returns a non-zero
  status, the library fallback is timed separately under the
  `agent="opencode_client"` label.
- **Remote sandboxes.** Sandboxed handovers observe the same histogram using the
  normalized agent name (for example, `agent="kimi2"`). The log entry
  `"Remote agent invocation finished"` summarizes the measured latency and
  whether a suggestion was produced.
- **Operational follow-up.** With durations bucketed per agent, SREs can set
  alerting thresholds (for example, high p95 latency for a single agent) or
  compare opencode fallback latencies against remote recommendations.

Because the histogram is labeled by agent, Grafana dashboards can chart time to
first suggestion per provider and detect regressions introduced by upstream API
changes.

## Configuration I/O Optimisations

- **Cached agent roster.** Loading `razar_ai_agents.json` now uses a
  timestamp-aware cache guarded by a re-entrant lock. Subsequent reads reuse the
  cached structure until the file’s modification time changes, eliminating
  repeated JSON parsing during escalation checks.
- **Cache invalidation.** Updating or restoring the active agent triggers
  `invalidate_agent_config_cache`, guaranteeing that handovers see fresh data
  immediately after configuration changes.

These changes reduce filesystem noise during steady-state boot sequences and
shorten latency for `_load_agent_state()` when retry storms occur.

## Recommendations

1. **Track baselines.** Establish per-component baseline histograms for
   `razar_ai_retry_duration_seconds` and the agent latency histogram, then alert
   on deviations beyond agreed service levels.
2. **Publish dashboards.** Add the new metrics to the existing observability
   dashboards so operators can drill into slow handovers without tailing logs.
3. **Future sampling.** Consider capturing the number of patched modules per
   attempt (available in `log_invocation`) to identify patterns where patches
   succeed but health checks continue to fail, signalling deeper component
   regressions.
