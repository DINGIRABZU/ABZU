# Monitoring

This stack launches Prometheus and Grafana alongside an NVIDIA GPU exporter.
Metrics include frames per second (FPS), API latency, and GPU utilization.

```bash
docker compose up
```

Prometheus listens on port `9090` and Grafana on `3000`.
