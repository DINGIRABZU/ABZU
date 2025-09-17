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
