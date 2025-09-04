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
