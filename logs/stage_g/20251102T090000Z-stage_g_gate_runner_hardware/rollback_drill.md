# Gate-Runner Hardware Rollback Drill

## Objective
Rehearse the sandbox-to-hardware rollback path for Stage G so the gate-runner replay can be halted within two steps if telemetry diverges.

## Sequence
1. Snapshot the hardware parity traces and store them beside the sandbox baseline.
2. Trigger `scripts/run_alpha_gate.sh --replay-from logs/stage_c/20251001T010101Z-readiness_packet` in sandbox mode to confirm the fallback path.
3. Issue `operator_api POST /alpha/stage-a3-gate-shakeout` to drain active sessions.
4. Flip the `gate_runner_enabled` flag to `false` in `crown_config/hardware.env` and confirm the operator console reports the sandbox identity as primary.
5. Restore sandbox connectors, replay the readiness packet, and re-enable hardware by applying the `gate_runner_enabled=true` patch once parity metrics match the sandbox baseline again.

## Telemetry Capture
- Hardware shutdown traces: `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/rollback_shutdown.log`
- Sandbox confirmation bundle: `logs/stage_c/20251001T010101Z-readiness_packet/replay_minutes.md`
- Operator console event log: `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/operator_console.json`

## Sign-off Trio
- Operator lead: @ops-team
- Hardware owner: @infrastructure-hardware
- QA reviewer: @qa-alliance

All three reviewers acknowledged the drill outcomes in `approvals.yaml`.
