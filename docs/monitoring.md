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
docker compose -f monitoring/docker-compose.yml up
```

Grafana listens on `http://localhost:3000` and Prometheus on `http://localhost:9090`.

## Timing metrics

Latency histograms are exported via Prometheus:

- `invocation_duration_seconds` – pattern invocation latency.
- `ritual_invocation_duration_seconds` – ritual lookup latency.
- `http_request_duration_seconds` – FastAPI request latency labelled by path and method.

All timings use `time.perf_counter()`. Higher values indicate slower operations
and can highlight performance bottlenecks.

