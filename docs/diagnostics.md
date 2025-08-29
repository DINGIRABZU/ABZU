# Diagnostic Scripts and Self-Healing Plan

This guide outlines the diagnostic scripts and the self-healing mechanisms
used to keep Spiral OS operational.

## Current Diagnostics

### Missing Modules
- `src/health/boot_diagnostics.py` imports modules listed in `src/health/essential_services.py`, attempting to auto-install or stub missing dependencies.
- `scripts/dependency_check.py` runs `pip check` and scores components based on missing optional dependencies.

### Log Integrity
- `scripts/replay_state.py` restores the latest backups, repairs simple JSON issues and quarantines unrecoverable log entries.
- `tests/test_interactions_jsonl_integrity.py` validates that interaction logs contain one JSON object per line.

### API Health
- `scripts/vast_check.py` polls `/health` and `/ready` endpoints and performs a WebRTC offer to ensure the server is ready.
- `razar/health_checks.py` retries failed API calls before falling back to restart logic.
- Shell helpers such as `start_spiral_os.py` call boot diagnostics before launching services and refuse to start when health checks fail.

## Desired Self-Healing Behavior

### Vital vs. Optional Modules
`src/health/essential_services.py` defines the `VITAL_MODULES` list used by
`boot_diagnostics.py`. Missing entries from this list (currently `server`,
`invocation_engine`, `emotional_state` and logging support) trigger an
immediate reinstall or stub because the system cannot function without them.
Modules not in `VITAL_MODULES` are considered optional. Their absence is
reported by `scripts/dependency_check.py` but does not block startup so the
system can continue in a reduced feature mode.

### Isolation of Failing Modules
`razar/quarantine_manager.py` moves unstable components into the top-level
`quarantine/` directory and records details in `docs/quarantine_log.md`. By
removing the failing module from the active path, the remaining services keep
running while a fix is developed. Quarantined modules can later be
reactivated once patched.

### Structured Failure Logging
The `agents.razar.mission_logger` module writes each failure and recovery
attempt as a JSON line to `logs/razar.log`. Entries capture the `event`,
`component`, `status`, `timestamp` and optional `details` fields. Helpers such
as `log_error`, `log_recovery` and `log_quarantine` provide a consistent,
machine-parsable audit trail.

## TODO
- [x] Distinguish between vital modules and optional components to prioritise recovery efforts.
- [x] Isolate failing modules so remaining services continue operating in a degraded but functional state.
- [x] Record detected failures and recovery attempts in structured logs for auditability.
- [x] Implement automated recovery routines to reinstall or stub missing modules during boot diagnostics.
- [x] Add log repair and quarantine for corrupted entries when replaying state from backups.
- [x] Introduce retry and restart logic when API health checks fail repeatedly.
