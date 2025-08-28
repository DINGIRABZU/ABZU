# RAZAR Agent

## Pre-creation Mandate

RAZAR serves as service 0 for ABZU. Before any servant boots, it wipes stale artifacts, builds a clean Python environment, and validates configuration. This ensures every run starts from a reproducible state.

Steps:
1. Remove cached virtual environments and temporary data.
2. Create an isolated environment from `razar_env.yaml`.
3. Run configuration checks and load secrets.

## Priority Boot and Health Management

Component priorities are read from `docs/system_blueprint.md` and `config/razar_config.yaml`. For each entry RAZAR:

1. Launches the component in priority order.
2. Executes the associated health check.
3. On failure, moves logs and artifacts to `quarantine/` and marks the step ❌ in `docs/Ignition.md`.

Successful components are marked ✅ and persisted to `logs/razar_state.json` so later runs resume from the last healthy step.

## Crown Handshake

Before the boot cycle, RAZAR sends a `mission_brief` to the CROWN LLM via `agents/razar/crown_handshake.py`. CROWN replies with available capabilities and readiness confirmation. During startup and after a failure, RAZAR contacts the relevant servant models and the CROWN LLM through `agents/razar/crown_link.py` to request patches or acknowledge health.

## Further Reading

- [Nazarick Agents](nazarick_agents.md)
- [System Blueprint](system_blueprint.md)
