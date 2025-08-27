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

## Timing metrics

Latency histograms are exported via Prometheus:

- `invocation_duration_seconds` – pattern invocation latency.
- `ritual_invocation_duration_seconds` – ritual lookup latency.
- `http_request_duration_seconds` – FastAPI request latency labelled by path and method.

All timings use `time.perf_counter()`. Higher values indicate slower operations
and can highlight performance bottlenecks.

