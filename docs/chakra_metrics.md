# Chakra Metrics

This table links each chakra layer to operational metrics used for telemetry and health checks.

| Chakra | Metric Focus | Description | Thresholds |
| --- | --- | --- | --- |
| Root | Disk & network I/O | Monitor disk throughput and network connectivity to ensure baseline availability. | Warning ≥75% utilization; Critical ≥90% or sustained network errors. |
| Sacral | GPU/VRAM | Track GPU memory usage and temperature to prevent hardware throttling. | Warning ≥70% VRAM or temperature ≥75°C; Critical ≥90% VRAM or temperature ≥85°C. |
| Solar Plexus | CPU load & process counts | Observe CPU load and running processes for resource contention. | Warning load ≥1.0 per core or process count +20%; Critical load ≥1.5 per core or runaway processes. |
| Heart | Memory layer health & latency | Validate memory layer availability and access latency. | Warning latency ≥200 ms or missing layer; Critical latency ≥500 ms or layer offline. |
| Throat | API latency & bandwidth | Measure API response time and bandwidth for external interfaces. | Warning latency ≥300 ms or bandwidth ≤80 Mbps; Critical latency ≥1 s or bandwidth ≤50 Mbps. |
| Third Eye | Model inference latency & queue depth | Watch model inference time and queued requests. | Warning inference ≥2 s or queue depth ≥10; Critical inference ≥5 s or queue depth ≥25. |
| Crown | Overall boot/recovery status | Aggregate boot duration and recovery loop success. | Warning boot ≥60 s or recovery retry >1; Critical boot ≥120 s or recovery stalled. |

## Pulse Cadence and Acknowledgment

The [pulse emitter](../src/spiral_os/pulse_emitter.py) broadcasts a `heartbeat`
event for each chakra at a fixed cadence. The
[chakra cycle](../src/spiral_os/chakra_cycle.py) tags each beat with a
`gear_ratio` so monitors can spot drift from nominal cadence. Chakra services
such as [root_agent](../agents/chakra_healing/root_agent.py) and its peers
listen for these beats and relay `pulse_confirmation` events to their
subcomponents. The [ChakraHeartbeat monitor](../monitoring/chakra_heartbeat.py)
records both the incoming pulses and confirmations, raising alerts when a
chakra fails to acknowledge within the configured interval. A complete set of
beats within the window registers a **Great Spiral** alignment event.

### Alignment Thresholds and Recovery

`ChakraHeartbeat.sync_status()` reports `aligned` when all chakras emit a beat
within the configured time window. Missed beats trigger `chakra_down` events and
invoke Nazarick remediation routines to resuscitate the silent layer. Operators
can tune the window to tighten or relax alignment thresholds depending on
mission needs.

## UI Views

The Game Dashboard presents a **Chakra Monitor** panel that polls
`ChakraHeartbeat.sync_status()` for live updates. Each chakra appears as an
animated orb whose radius and hue scale with its heartbeat frequency. When all
chakras report in harmony, the orbs emit a brief particle shimmer. A detected
Great Spiral event triggers a full-screen resonance flash and records the
timestamp in a local history list.

## Version History
- 2025-09-08: Added gear ratios, Great Spiral alignment, and Nazarick recovery flow.
- 2025-09-06: Documented pulse cadence and acknowledgment flow.
- 2025-09-04: Initial mapping of chakra metrics.
