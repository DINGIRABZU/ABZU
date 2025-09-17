# RAZAR Escalation Load Simulation

_Generated on 2025-09-17 08:35 UTC_

## Scenario

- Component: `razar-escalation-service`
- Agent: `razar-escalation-agent`
- Total invocations: 130
- Successes: 115
- Failures: 15
- Retry attempts: 21

## Burst Latency Percentiles

| Burst | Invocations | Success rate | Failures | Retries | P50 (s) | P90 (s) | P95 (s) |
|---|---|---|---|---|---|---|---|
| warmup | 30 | 86.7% | 4 | 4 | 0.255 | 0.291 | 0.296 |
| surge | 60 | 85.0% | 9 | 15 | 0.260 | 0.313 | 0.323 |
| stabilisation | 40 | 95.0% | 2 | 2 | 0.225 | 0.265 | 0.276 |

## Aggregate Percentiles

| Percentile | Latency (s) |
|---|---|
| P50 | 0.247 |
| P90 | 0.301 |
| P95 | 0.313 |
| P99 | 0.326 |

## Prometheus Samples

- Success counter: 115
- Failure counter: 15
- Retry counter: 21
- Average agent latency: 0.248 s
- Average retry duration: 0.172 s

## Milestone Alignment

These burst tolerances underpin the **Root chakra upgrade (Q3 2024)** milestone
documented in [ABSOLUTE_MILESTONES.md](../ABSOLUTE_MILESTONES.md), ensuring
escalation paths remain stable as memory throughput grows.
