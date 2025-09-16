# Metrics Catalog

| Metric | Type | Labels | Description | Dashboard |
| --- | --- | --- | --- | --- |
| `service_boot_duration_seconds` | Gauge | `service` | Seconds from process start to readiness | Startup overview |
| `narrative_events_total` | Counter | _none_ | Total stories logged via narrative API | Narrative throughput |
| `servant_health_status` | Gauge | `servant` | 1=healthy, 0=unhealthy per servant model | Servant health |
| `chakra_cycles_total` | Counter | `chakra` | Completed heartbeat-confirmation cycles | Chakra Pulse |
| `chakra_cycle_duration_seconds` | Gauge | `chakra` | Seconds between heartbeat and confirmation | Chakra Pulse |
| `neoabzu_vector_init_total` | Counter | _none_ | Vector service Init RPCs processed | Vector service |
| `neoabzu_vector_search_total` | Counter | _none_ | Vector service Search RPCs processed | Vector service |
| `neoabzu_vector_init_latency_seconds` | Histogram | _none_ | Init RPC latency distribution | Vector service |
| `neoabzu_vector_search_latency_seconds` | Histogram | _none_ | Search RPC latency distribution | Vector service |
| `neoabzu_vector_store_size` | Gauge | _none_ | Embeddings loaded across vector shards | Vector service |

