# Copresence Dashboard

This Grafana dashboard surfaces real‑time copresence signals for operators.
It focuses on boot health, narrative flow and error rates across core agents.

## Panels

- **Service Boot Time** – `service_boot_duration_seconds{service="crown|bana|memory"}` displayed as a gauge for startup latency.
- **Narrative Throughput** – rate of `narrative_throughput_total` per service graphed over 5 m to show story activity.
- **Error Counts** – `service_errors_total` broken down by service to highlight failing components.

## Import

```json
{
  "title": "Copresence",
  "panels": [
    {"type": "gauge", "targets": [{"expr": "service_boot_duration_seconds"}]},
    {"type": "timeseries", "targets": [{"expr": "rate(narrative_throughput_total[5m])"}]},
    {"type": "stat", "targets": [{"expr": "service_errors_total"}]}
  ]
}
```

Load the JSON above via **Dashboard ➜ Import** in Grafana and adjust
Prometheus datasource names as needed.
