# Monitoring

This stack launches Prometheus, Grafana, Node Exporter, cAdvisor, and an
NVIDIA GPU exporter. Metrics include CPU, memory, disk, network, container
statistics, frames per second (FPS), API latency, and GPU utilization.

```bash
docker compose up
```

Prometheus listens on port `9090` and Grafana on `3000`. Node Exporter exposes
metrics on `9101`, cAdvisor on `8080`, and the DCGM GPU exporter on `9400`.

## Watchdog

`watchdog.py` tracks CPU, memory, file descriptors, and system network I/O for
configured services. Alerts are printed to the console and written as JSON
under `alerts/`. When a threshold is exceeded, the script optionally exposes
metrics for Prometheus on port `9100` and attempts service restarts via
`os_guardian.action_engine`.

Run the watchdog with:

```bash
python monitoring/watchdog.py
```

Edit the `SERVICES` dictionary in the script to match local process names and
restart commands.

## Pytest Metrics

Running the test suite exports `pytest_metrics.prom` in this directory.  The file
contains `pytest_test_duration_seconds` and `pytest_test_failures_total` metrics
for Prometheus scraping.

## Alpha Gate Metrics

`scripts/run_alpha_gate.sh` now drops `monitoring/alpha_gate.prom` and a
structured JSON summary every run. Prometheus can scrape the textfile directly
or you can push the contents into a shared Pushgateway instance.

## Boot Metrics

`razar.boot_orchestrator` exports `monitoring/boot_metrics.prom` with gauges for
first-attempt successes, total retries, and the end-to-end boot duration. The
Stage A gate copies the file into `logs/alpha_gate/boot_metrics.prom`, and the
CI pipeline publishes it with the other Alpha gate artifacts. Point a Node
Exporter textfile collector at the directory to surface the gauges on the Boot
Ops Grafana board (panels titled *Boot First Attempt Successes*, *Boot Retry
Attempts*, and *Boot Total Time*).

## Stage B rehearsal scheduler

Run `python scripts/rehearsal_scheduler.py` to orchestrate the Stage B rehearsal
workflow or trigger the automated pipeline defined in
`deployment/pipelines/stage_b_rehearsal.yml` via
`spiral-os pipeline deploy stage_b_rehearsal`. Each execution:

- Executes `scripts/health_check_connectors.py` (including remote agent probes)
  and writes the JSON results to
  `monitoring/stage_b/<run-id>/health_checks.json`.
- Invokes `scripts/stage_b_smoke.py` to capture the full smoke-test payload,
  new credential rotation timestamps, and the doctrine verdict. Artifacts are
  persisted under `monitoring/stage_b/<run-id>/` alongside a consolidated
  `rehearsal_summary.json` bundle.
- Emits `monitoring/stage_b/<run-id>/rehearsal_status.prom`, a Prometheus
  textfile that surfaces health, smoke-test, and rotation coverage gauges for
  alerting dashboards. The latest run is mirrored to
  `monitoring/stage_b/latest/` so Grafana panels and alert rules can scrape the
  most recent status during the 48-hour credential drill.

The pipeline archives the entire `monitoring/stage_b/` directory as
`logs/stage_b_rehearsal_artifacts.tgz` after the scheduler completes so ops
teams can attach the run artifacts to Stage B readiness reviews.

### File-based scraping

1. Add a [`textfile` collector job](https://prometheus.io/docs/instrumenting/writing_exporters/#textfile-collector)
   to your Prometheus configuration.
2. Symlink or copy `monitoring/alpha_gate.prom` into the directory that the
   collector watches (for example `/var/lib/node_exporter/textfile_collector/`).
3. Reload Prometheus and import the updated `monitoring/grafana-dashboard.json`
   to visualize phase timing, success, and coverage panels.

### Pushgateway

1. Start a Pushgateway instance reachable from your automation host.
2. After running the gate, push the metrics file:

   ```bash
   cat monitoring/alpha_gate.prom | curl --data-binary @- \
     http://pushgateway.example.com:9091/metrics/job/alpha-gate
   ```

3. Point Grafana or alerting rules at the Pushgateway-hosted series to watch
   coverage and phase success trends between promotions.
