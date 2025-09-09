# Monitoring

The application writes JSON-formatted logs to `logs/INANNA_AI.log`. The file
rotates when it reaches roughly 10 MB, keeping seven backups
(`INANNA_AI.log.1`, `INANNA_AI.log.2`, ...).

## Tailing logs

```bash
tail -F logs/INANNA_AI.log
```

Use `tail -F` to follow the active log file across rotations. The output uses
JSON, making it easy to filter with tools such as `jq`:

```bash
tail -F logs/INANNA_AI.log | jq '.duration? // empty'
```

## Log fields

Several JSON fields are emitted by the system:

- `symbols` and `emotion` from `invocation_engine.invoke`.
- `ritual` from `invocation_engine.invoke_ritual`.
- `path` and `method` for HTTP requests handled by the FastAPI middleware.
- `duration` in seconds for any of the above operations.

## RAZAR health

Launch the RAZAR orchestrator before scraping metrics so it can supervise
services and report status:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

RAZAR provides a `/health` endpoint exposing an environment hash and heartbeat.
Probe it directly or via Prometheus to verify the orchestrator is running:

```bash
curl http://localhost:9300/health
```

If RAZAR cannot restart components, rebuild the virtual environment and rerun
the manager. Deleting the `.state` file next to the configuration forces a
full restart cycle.

## Chakra status board

`monitoring/chakra_status_board.py` aggregates heartbeat frequencies and
component versions. Query the JSON endpoint for a snapshot or scrape the
metrics endpoint with Prometheus:

```bash
curl http://localhost:8000/chakra/status
```

A status of `out_of_sync` or a frequency near zero indicates a stalled chakra.
Version fields reveal outdated components that may require redeployment.

## Chakra Pulse panel

`monitoring/chakra_heartbeat.py` exports per-chakra cycle metrics that report
how quickly each layer confirms its heartbeat. See [Chakra Heartbeat](chakra_heartbeat.md) for pulse timing and chakra mapping details:

- `chakra_cycles_total` – total completed heartbeat-confirmation cycles per chakra
- `chakra_cycle_duration_seconds` – seconds between a heartbeat and its confirmation

The [Game Dashboard](ui/game_dashboard.md) renders these metrics in the
[Chakra Pulse](ui/chakra_pulse.md) panel. Colored orbs pulse at the reported
frequencies, an "aligned" glow marks synchronized chakras, and the panel lists
the timestamps of recent `great_spiral` events for historical context.

## Agent status panel

`monitoring/agent_status_endpoint.py` summarizes heartbeat timestamps and
related state for each agent. The **Agent Status** panel in the
[Game Dashboard](ui/game_dashboard.md) polls `/agents/status` and lists every
agent with its last heartbeat, most recent action, and chakra alignment marker.
Arcade deployments can use [Arcade Mode](ui/arcade_mode.md) for a retro
presentation of the same telemetry:

```bash
curl http://localhost:8000/agents/status
```

Use this panel to quickly spot stalled agents or unexpected actions during
runtime.

## Self-healing panel

`monitoring/self_healing_ledger.py` writes recovery events to
`logs/self_healing.json`. `monitoring/self_healing_endpoint.py` exposes the
current ledger via `/self-healing/ledger` and streams new entries over the
`/self-healing/updates` WebSocket. The **Self Healing** panel in the
[Game Dashboard](ui/game_dashboard.md) lists recent ledger entries and highlights
components with active repairs.

```bash
websocat ws://localhost:8000/self-healing/updates
curl http://localhost:8000/self-healing/ledger
```

Use this telemetry to monitor recovery progress and confirm failed components
are restored.

## Boot history

Component activity is written to `logs/razar.log` in JSON lines. Refer to the
[logging guidelines](logging_guidelines.md) for event types and usage. To
reconstruct the boot history and identify failures chronologically, run:

```bash
python -m razar timeline
```

## Quarantine log

Components that repeatedly fail their health checks are quarantined by the
runtime manager. The affected module is moved under the repository-level
`quarantine/` directory and an entry is appended to
`docs/quarantine_log.md` with the failure reason and timestamp. Remove the
corresponding JSON file and add a `resolved` line to the log once the component
has been fixed.

## Status dashboard

Use the status dashboard for a quick snapshot of the current boot attempt and
component states:

```bash
python -m razar.status_dashboard
```

The output lists each component with its priority and criticality and provides
links to the quarantine log and boot history.

## Mission lifecycle metrics

`agents.razar.mission_logger` appends a JSON line for each lifecycle change
recorded during a mission. These entries can be transformed into metrics for
alerting and dashboards.

Count how many times components entered recovery mode:

```bash
jq -r 'select(.event=="recovery") | .component' logs/razar.log | wc -l
```

Expose per-event counters to Prometheus using the textfile collector:

```bash
jq -r '.event' logs/razar.log | sort | uniq -c | \
  awk '{printf "mission_events_total{event=\"%s\"} %s\n", $2,$1}' \
  > /var/lib/node_exporter/mission.prom
```

Correlate these metrics with the remediation flow described in the
[Recovery Playbook](recovery_playbook.md) to verify that failed components are
patched and resolved in order.

## Health check metrics

`agents/razar/health_checks.py` performs service probes with per-service latency
thresholds. When the `prometheus_client` package is installed the script
exposes metrics on port `9350`:

```bash
python -m agents.razar.health_checks --interval 30
```

Metrics exported:

- `service_health_status` – `1` when healthy, `0` when a probe fails.
- `service_health_latency_seconds` – latency for each probe.

Add the endpoint to the Prometheus configuration:

```yaml
- job_name: 'razar-health'
  static_configs:
    - targets: ['razar-health:9350']
```

Start the bundled monitoring stack to explore dashboards in Grafana:

```bash
docker compose -f monitoring/docker-compose.yml up -d
```

The stack launches Prometheus, Grafana, Node Exporter, cAdvisor, and the DCGM
GPU exporter. Prometheus labels each target with its chakra layer as defined in
`monitoring/prometheus.yml` so metrics are grouped by `chakra=<layer>`.

Grafana listens on `http://localhost:3000` and Prometheus on `http://localhost:9090`.

### Resource dashboards

The docker-compose stack also launches resource exporters:

- **Node Exporter** gathers CPU, RAM, disk, and network metrics from the host.
- **cAdvisor** exposes container-level statistics.
- **gpu-exporter** (DCGM) publishes GPU utilization and memory data.

Import `monitoring/grafana-dashboard.json` into Grafana to view panels for
these metrics. CPU, memory, disk, network, and GPU graphs are preconfigured.
The `monitoring/watchdog.py` script augments these dashboards with system
network throughput using `psutil.net_io_counters`.

### Service metrics

Core layers now expose Prometheus gauges for CPU, memory, GPU, and latency.
`crown_router`, `agents.razar.health_checks`, `agents.bana.bio_adaptive_narrator`,
and `memory.narrative_engine` publish:

- `service_cpu_usage_percent`
- `service_memory_usage_bytes`
- `service_gpu_memory_usage_bytes`
- `service_request_latency_seconds`

Each metric is labelled by `service` so Grafana panels can display resource
usage and latency for Crown, RAZAR, Bana, and Memory side by side. Import
`monitoring/grafana-dashboard.json` to visualize these metrics.

## Timing metrics

Latency histograms are exported via Prometheus:

- `invocation_duration_seconds` – pattern invocation latency.
- `ritual_invocation_duration_seconds` – ritual lookup latency.
- `http_request_duration_seconds` – FastAPI request latency labelled by path and method.

All timings use `time.perf_counter()`. Higher values indicate slower operations
and can highlight performance bottlenecks.

