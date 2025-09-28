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
| `operator_api_transport_latency_ms` | Histogram | `transport`, `operation` | Operator API latency split by transport and operation | Operator transport pilot |
| `operator_api_transport_errors_total` | Counter | `transport`, `operation`, `reason` | Operator API error counts including handshake and dispatcher failures | Operator transport pilot |
| `operator_api_transport_fallback_total` | Counter | `transport`, `operation` | Operator API fallback executions from gRPC to REST | Operator transport pilot |
| `alpha_gate_phase_start_timestamp_seconds` | Gauge | `phase` | UTC start time for each Alpha gate phase | Alpha gate |
| `alpha_gate_phase_end_timestamp_seconds` | Gauge | `phase` | UTC completion time for each Alpha gate phase | Alpha gate |
| `alpha_gate_phase_duration_seconds` | Gauge | `phase` | Elapsed seconds for each Alpha gate phase | Alpha gate |
| `alpha_gate_phase_success` | Gauge | `phase` | 1 when the Alpha gate phase succeeded, 0 otherwise | Alpha gate |
| `alpha_gate_phase_exit_code` | Gauge | `phase` | Exit code captured from the Alpha gate phase | Alpha gate |
| `alpha_gate_phase_skipped` | Gauge | `phase` | 1 when the phase was skipped explicitly | Alpha gate |
| `alpha_gate_overall_success` | Gauge | _none_ | 1 when all executed Alpha gate phases succeeded | Alpha gate |
| `alpha_gate_coverage_percent` | Gauge | _none_ | Overall line coverage percentage from the gate run | Alpha gate |
| `alpha_gate_coverage_lines_covered` | Gauge | _none_ | Total covered lines from coverage.py during the gate run | Alpha gate |
| `alpha_gate_coverage_statements` | Gauge | _none_ | Total measured statements from coverage.py during the gate run | Alpha gate |
| `alpha_gate_coverage_missing_lines` | Gauge | _none_ | Remaining uncovered lines from coverage.py during the gate run | Alpha gate |
| `crown_replay_divergences_total` | Gauge | _none_ | Crown replay scenarios that diverged from their stored baselines | Alpha gate |
| `crown_replay_duration_seconds` | Gauge | _none_ | Wall-clock seconds spent executing the replay regression suite | Alpha gate |
| `crown_replay_scenarios_total` | Gauge | _none_ | Number of recorded Crown scenarios exercised during the regression | Alpha gate |
| `razar_boot_first_attempt_success_total` | Gauge | _none_ | Components that succeeded on their first attempt in the latest boot run | Boot Ops |
| `razar_boot_retry_total` | Gauge | _none_ | Aggregate retry count recorded during the latest boot run | Boot Ops |
| `razar_boot_total_time_seconds` | Gauge | _none_ | Wall-clock duration of the latest boot sequence in seconds | Boot Ops |
| `razar_boot_success_rate` | Gauge | _none_ | Success ratio recorded for the most recent boot sequence | Boot Ops |
| `razar_boot_component_total` | Gauge | _none_ | Components evaluated during the most recent boot run | Boot Ops |
| `razar_boot_component_success_total` | Gauge | _none_ | Components that completed successfully in the most recent boot run | Boot Ops |
| `razar_boot_component_failure_total` | Gauge | _none_ | Components that failed in the most recent boot run | Boot Ops |

