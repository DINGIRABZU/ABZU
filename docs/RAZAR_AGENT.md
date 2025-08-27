# RAZAR Agent

RAZAR acts as service 0 in the ABZU stack. It verifies the runtime
environment, sequenced component priorities, and continually rewrites
[Ignition.md](Ignition.md) with health markers so operators can track
startup progress. The agent forms a feedback loop with CROWN LLM to heal
faulty modules and ensures the system can cycle back to a ready state
without manual intervention.

## Perpetual Ignition Loop

RAZAR runs a perpetual ignition loop that:

1. Reads component priorities from `Ignition.md` and
   `config/razar_config.yaml`.
2. Builds the dedicated virtual environment and installs dependencies
   defined in `razar_env.yaml`.
3. Boots each component in priority order using
   `agents/razar/runtime_manager.py`.
4. Probes `/ready` and `/health` endpoints via
   `agents/razar/health_checks.py`.
5. Rewrites the status column in `Ignition.md` (✅/⚠️/❌) and loops back to
   monitor the stack.  The loop never exits on its own—it continually
   verifies that previously healthy services stay responsive.

## Adaptive Startup Orchestrator

The `razar/adaptive_orchestrator.py` helper experiments with different
component start orders defined in `component_priorities.yaml`.  Each run
records the overall time to reach a ready state and any failure points, then
stores the results in `logs/razar_boot_history.json` so future launches can
reuse the quickest sequence.

### CLI Options

- `--strategy` – choose `priority` (default) to start components in declared
  order or `random` to explore shuffled sequences.
- `--resume` – reuse the best sequence from previous history entries.

## CROWN LLM Diagnostics and Patching

When a component fails a health check, RAZAR collects logs and test
artifacts and asks the CROWN LLM for repair guidance.  The
`agents/razar/code_repair.py` helper submits the failing module and error
context to the LLM, receives a patch suggestion, and validates the result
in a sandbox.  Successful patches are committed back to the repository
and the component is marked ready for reactivation.

## Shutdown–Repair–Restart Handshake

RAZAR performs a handshake with unhealthy services:

1. **Shutdown** – instruct the component to stop gracefully and move its
   metadata to `quarantine/`.
2. **Repair** – run diagnostics, solicit a patch from the CROWN LLM, and
   rerun the module's tests.
3. **Restart** – if tests pass, call
   `quarantine_manager.reactivate_component` and relaunch via the runtime
   manager.  Status in `Ignition.md` returns to ✅.

This handshake guarantees that faulty code is isolated, repaired, and
brought back online under explicit operator control.

## Further Reading

- [System Blueprint](system_blueprint.md)
- [Nazarick Agents](nazarick_agents.md)
- [Developer Onboarding](developer_onboarding.md)
