# Diagnostic Scripts and Self-Healing Plan

## Current Diagnostics

### Missing Modules
- `src/health/boot_diagnostics.py` imports modules listed in `src/health/essential_services.py` and reports failures during startup.
- `scripts/dependency_check.py` runs `pip check` and scores components based on missing optional dependencies.

### Log Integrity
- `scripts/replay_state.py` restores the latest backups and skips malformed JSON entries when rebuilding vector memory.
- `tests/test_interactions_jsonl_integrity.py` validates that interaction logs contain one JSON object per line.

### API Health
- `scripts/vast_check.py` polls `/health` and `/ready` endpoints and performs a WebRTC offer to ensure the server is ready.
- Shell helpers such as `start_spiral_os.py` call boot diagnostics before launching services and refuse to start when health checks fail.

## Desired Self-Healing Behavior
- Distinguish between vital modules and optional components to prioritise recovery efforts.
- Isolate failing modules so remaining services continue operating in a degraded but functional state.
- Record detected failures and recovery attempts in structured logs for auditability.

## TODO
- [ ] Implement automated recovery routines to reinstall or stub missing modules during boot diagnostics.
- [ ] Add log repair and quarantine for corrupted entries when replaying state from backups.
- [ ] Introduce retry and restart logic when API health checks fail repeatedly.
