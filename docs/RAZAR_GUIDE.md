# RAZAR Guide

## Vision
RAZAR bootstraps ABZU services in a reproducible virtual environment and negotiates startup handshakes with the Crown stack.

## Architecture
- Creates Python environments per chakra layer.
- Launches components based on `boot_config.json` and verifies readiness with `health_checks.py`.
- Logs mission state to `logs/razar_state.json`.

## Deployment
```bash
python -m razar.boot_orchestrator --mission demo
```
Requires `pyyaml`, `prometheus_client`, `websockets`, and a reachable `CROWN_WS_URL`.

## Configuration Schemas
- `boot_config.json` — component list and health probes.
- `razar_env.yaml` — layer-specific dependencies.
- `logs/razar_state.json` — runtime state record.

## Example Runs
```bash
python -m razar.crown_handshake path/to/brief.json
```

## Monitoring & Recovery
RAZAR emits lifecycle events to `logs/razar.log` via
`agents.razar.mission_logger`. Each JSON line records the event, component,
status, timestamp, and optional details. Use these entries to track recovery
progress and feed metrics collectors or dashboards.

Count recovery attempts:

```bash
jq -r 'select(.event=="recovery") | .component' logs/razar.log | wc -l
```

Review the full remediation flow in the [Recovery Playbook](recovery_playbook.md).

## Cross-Links
- [System Blueprint](system_blueprint.md)
- [Deployment Guide](deployment.md)
- [Monitoring Guide](monitoring.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.3.0 | 2025-10-17 | Structured lifecycle logging and recovery metrics. |
| 0.2.2 | 2025-09-21 | Expanded remote assistance workflow and patch logging. |
| 0.1.0 | 2025-08-30 | Initial release of RAZAR runtime orchestrator. |
