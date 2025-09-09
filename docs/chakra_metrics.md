# Chakra Metrics

The chakra status board aggregates heartbeat signals and component versions
for operators. It combines data from `monitoring.chakra_heartbeat` and
`agents.razar.state_validator` to show each chakra's pulse and the software
release supervising it. Pulse timing and layer roles are described in
[Chakra Heartbeat](chakra_heartbeat.md).

## Viewing metrics

Run the board and query the JSON endpoint:

```bash
curl http://localhost:8000/chakra/status
```

The response includes the alignment status, per-chakra pulse frequency in
hertz, and component versions. Prometheus can scrape the same data from
`/metrics`.

## Interpretation

- **Misaligned pulses** (`status` is `out_of_sync`) indicate that one or more
  chakras missed recent heartbeats.
- **Stalled pulses** (frequency near `0`) suggest the chakra's component is not
  responding.
- **Outdated versions** in the `versions` section highlight components that
  may require redeployment.

Operators review these signals to determine when to restart services or
investigate disruptions.

## Agent heartbeat metrics

Operators can inspect individual agent heartbeats through
`monitoring.agent_status_endpoint`. The endpoint reports the last heartbeat
timestamp, most recent action, and chakra alignment for each agent:

```bash
curl http://localhost:8000/agents/status
```

These metrics feed the Agent Status panel and help identify agents that have
stopped emitting heartbeats.
