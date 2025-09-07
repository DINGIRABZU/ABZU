# Recovery Playbook

This playbook outlines how RAZAR restores service after a component failure.
Recurring problems and their fixes are cataloged in the
[Error Registry](error_registry.md).

Connector-specific recovery steps for chakra-tagged signals and heartbeat
propagation are documented in
[communication_interfaces.md](communication_interfaces.md#recovery-flows).

## Boot sequence

1. The boot orchestrator launches components in priority order.
2. Each launch runs a service-specific probe from `agents.razar.health_checks`.
3. On failure the orchestrator retries the component locally a limited number of times.
4. If local retries fail, `ai_invoker.handover(component, error, use_opencode=True)` requests an automated patch. Each attempt is logged to `logs/razar_ai_invocations.json`.
5. When run with `--long-task`, the orchestrator keeps invoking the handover until the component passes its health check or the operator aborts with `Ctrl+C`. Each attempt and resulting patch is appended to `logs/razar_long_task.json`.
6. Without `--long-task`, returned patches are applied and the health check reruns until it succeeds or the remote attempt limit is reached.
7. After exhausting remote attempts or an operator abort, the component's metadata is quarantined under `quarantine/` and an entry is appended to `docs/quarantine_log.md`.
8. The last successful component is recorded in `logs/razar_state.json` so subsequent runs resume from that point.

## Restoring a component

1. Investigate the failure using data in `docs/quarantine_log.md` and any artifacts in `quarantine/`.
2. Apply fixes and verify them.
3. Delete the component's file from `quarantine/` and log a `resolved` entry.
4. Rerun the boot orchestrator; it skips resolved components and continues from the last healthy stage.

## Monitoring

`agents.razar.health_checks` exposes Prometheus metrics when `prometheus_client` is installed. These probes allow external systems to track service readiness and latency during recovery.

## Snapshot Recovery

The memory spine maintains timestamped dumps of every chakra layer. On
restart RAZAR selects the newest snapshot and replays heartbeat logs from
`logs/heartbeat.log` to rebuild sessions and pending events. This process
lets the system resume from the exact point of failure. Architectural
context lives in the [System Blueprint](system_blueprint.md#memory-spine)
and [Blueprint Spine](blueprint_spine.md#memory-spine).

## Agent-specific recovery

Heartbeat polling feeds `chakra_down` events to the agent assigned to the
affected layer. Each agent runs a dedicated recovery script—`root_restore_network.sh`
resets networking for the Root layer, `sacral_gpu_recover.py` flushes GPU
tasks for Sacral, and other utilities live under `scripts/chakra_healing/`.
The polling loop is driven by the
[Chakra Cycle Engine](system_blueprint.md#chakra-cycle-engine), whose
propagation path and self-healing flow are mapped in the
[Blueprint Spine](blueprint_spine.md#heartbeat-propagation-and-self-healing)
and detailed in the
[Chakra Architecture](chakra_architecture.md#chakra-cycle-engine).
When errors persist beyond these hooks,
`scripts/escalation_notifier.py` scans log files for recurring failures,
posts an alert to `/operator/command`, and records the event in
`logs/operator_escalations.jsonl`.

## Failure Pulses

RAZAR emits scheduled **failure pulses** during idle windows to validate the
recovery pipeline. Each pulse simulates a component fault and writes an entry to
`logs/failure_pulses.jsonl`. The targeted service is expected to fail fast and
re-enter the standard boot sequence, proving the health checks and orchestration
hooks remain functional.

## Nazarick Resuscitation

If a pulse or live outage silences a chakra, the `chakra_down` event routes to
the assigned [Nazarick agent](nazarick_agents.md). That servant replays the
component’s launch ritual, restores missing state from the
[Memory Spine](system_blueprint.md#memory-spine), and reports progress back to
`/operator/command` until the heartbeat returns.

## Patch Rollbacks

All applied patches are logged in `logs/patch_history.jsonl`. When a patch
introduces regressions, run `scripts/rollback_patch.py <component>` to restore
the previous revision. The rollback records a `reverted` event in the history
log and the component re-enters the boot queue for validation.

## Opencode Integration

Automate patch generation by installing the Opencode CLI:

```bash
pip install opencode-cli
```

Call `razar.ai_invoker.handover(component, error, use_opencode=True)` with the
failure details. The failure context is piped to `opencode run --json` and any
patch suggestions are applied through `code_repair.repair_module`. The boot
orchestrator repeats this handover and health check cycle until the component
recovers or the remote attempt limit is reached. Enable long task mode with
`--long-task` to keep requesting patches indefinitely; abort with `Ctrl+C` to
halt the loop. Every long task attempt is written to `logs/razar_long_task.json`.

## Kimi-powered repairs

Set these variables to delegate repairs through Kimi:

- `OPENCODE_BACKEND=kimi`
- `KIMI_K2_URL=<your K2 endpoint>`

See [Kimi Integration](tools/kimi_integration.md) for step-by-step instructions.

```python
import os
from agents.razar import ai_invoker

os.environ["OPENCODE_BACKEND"] = "kimi"
os.environ["KIMI_K2_URL"] = "https://k2.example/api"

ai_invoker.handover("crown_router", "Health check failed", use_opencode=True)
```

If Kimi returns a patch, it is applied and the boot sequence resumes.

## Version History

- 2025-09-18: Added snapshot recovery using memory spine and heartbeat logs.
- 2025-09-07: Documented failure pulses, Nazarick resuscitation flow, and patch rollback procedures.
