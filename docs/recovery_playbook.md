# Recovery Playbook

This playbook outlines how RAZAR restores service after a component failure.

## Boot sequence

1. The boot orchestrator launches components in priority order.
2. Each launch runs a service-specific probe from `agents.razar.health_checks`.
3. On failure the orchestrator retries the component a limited number of times.
4. After exhausting retries, the component's metadata is quarantined under `quarantine/` and an entry is appended to `docs/quarantine_log.md`.
5. The last successful component is recorded in `logs/razar_state.json` so subsequent runs resume from that point.

## Restoring a component

1. Investigate the failure using data in `docs/quarantine_log.md` and any artifacts in `quarantine/`.
2. Apply fixes and verify them.
3. Delete the component's file from `quarantine/` and log a `resolved` entry.
4. Rerun the boot orchestrator; it skips resolved components and continues from the last healthy stage.

## Monitoring

`agents.razar.health_checks` exposes Prometheus metrics when `prometheus_client` is installed. These probes allow external systems to track service readiness and latency during recovery.
