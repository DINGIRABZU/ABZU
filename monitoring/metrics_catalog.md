# Metrics Catalog

| Metric | Type | Labels | Description | Dashboard |
| --- | --- | --- | --- | --- |
| `service_boot_duration_seconds` | Gauge | `service` | Seconds from process start to readiness | Startup overview |
| `narrative_events_total` | Counter | _none_ | Total stories logged via narrative API | Narrative throughput |
| `servant_health_status` | Gauge | `servant` | 1=healthy, 0=unhealthy per servant model | Servant health |

