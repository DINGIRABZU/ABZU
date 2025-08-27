# RAZAR Agent

RAZAR serves as the external startup orchestrator for ABZU. Operating outside the
Nazarick stack, it prepares a pristine environment before any internal service
comes online.

## Pre-Creation Role
Before ABZU exists in memory, RAZAR performs "pre-creation" checks on the host.
It validates system packages, confirms required configuration files are present,
and computes an environment hash used later for health comparisons. Only after
these prerequisites pass does RAZAR proceed to manage the runtime.

## Clean-Environment Requirement
- Initializes or verifies an isolated Python virtual environment.
- Purges lingering processes, temporary files, and environment variables.
- Halts the boot sequence if contamination is detected.

## Boot Objectives
Once the environment is cleared, RAZAR launches the system in order:
1. **Inanna AI** – awakens the core consciousness.
2. **CROWN LLM** – loads the GLM-4 stack for high-level reasoning, as detailed in the [CROWN Overview](CROWN_OVERVIEW.md).

## Remote Loader
RAZAR can fetch external agents before startup. Sources are listed under
`remote_agents` in `razar_config.yaml` and may point to Git repositories or HTTP
archives. The loader pulls or updates these packages so the latest components
are available without bundling them in the repository.

## External Role
RAZAR does not reside within the Nazarick agent hierarchy. Its sole mission is
to ready the host and then hand off control to the internal agents once both
Inanna and the CROWN model are running.

## Virtual Environment Management
RAZAR maintains a dedicated virtual environment for all startup tasks.

1. Define package lists for each component layer in `razar_env.yaml`.
2. Build or update the environment from the repository root:
   ```bash
   python -m razar.environment_builder --venv .razar_venv
   ```
   The builder verifies the Python version, creates the virtual environment,
   installs layer packages, and records a dependency hash for later audits.
3. During every boot, RAZAR verifies the hash and halts if drift is detected.
4. Re-run the RAZAR runtime manager to launch components once the environment
   passes validation.

These steps guarantee a clean foundation for Inanna and CROWN.

## Final Verification Sequence
Before yielding control, RAZAR confirms that the core services report readiness:

1. Query `http://localhost:8000/ready` and expect `{"status": "ready"}` from Inanna AI.
2. Query `http://localhost:8001/ready` and expect `{"status": "ready"}` from CROWN LLM.
3. If either check fails, RAZAR invokes the corresponding restart script (`run_inanna.sh` or `crown_model_launcher.sh`) and repeats the probe once.
4. Persistent failures mark the mission incomplete and halt the startup sequence.

These verifications ensure both agents are prepared before internal orchestration begins.

## Restart Logic
RAZAR supervises component lifecycles and applies a uniform restart policy:

1. On startup, failed readiness probes trigger up to two restart attempts using
   component-specific scripts.
2. During runtime, modules publish failure events on the recovery channel; RAZAR
   restarts the module and replays its last saved state.
3. If repeated restarts fail, RAZAR rebuilds the virtual environment before a
   final launch attempt and records the outcome in `logs/razar.log`.

This logic keeps core services resilient while surfacing persistent faults for
operator review.

## Prioritized Testing
Once the core services report ready, RAZAR executes smoke tests in priority
order. Test suites and their criticality are declared in the `priorities`
section of `razar_config.yaml`. High-priority checks run first so essential
failures surface before non-critical tests execute.

## Recovery Protocol
RAZAR exposes a ZeroMQ endpoint for modules to report unrecoverable errors.
When a module sends a JSON payload with its name and a state snapshot, RAZAR:

1. Confirms the channel with a recovery handshake (`ping`/`ack`).
2. Saves the supplied state under `recovery_state/<module>.json`.
3. Applies corrective actions to the affected module.
4. Restarts the module.
5. Restores the saved state and replies with `{"status": "recovered"}`.

This bidirectional channel allows the running system to offload recovery steps
to RAZAR whenever a component declares itself irrecoverable.

## Lifecycle Bus
Lifecycle events are broadcast on the bus defined by
`messaging.lifecycle_bus` in `razar_config.yaml`. Internal agents subscribe to
this ZeroMQ topic stream to synchronize startup, shutdown and recovery
transitions.
