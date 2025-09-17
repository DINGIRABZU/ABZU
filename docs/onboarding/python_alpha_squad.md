# Python Alpha Squad Dossier

The Python Alpha Squad stewards ABZU's mission-critical boot and recovery toolchain. The team owns the Python-facing layers that wake the stack, triage failures, and delegate complex repairs to remote agents. Use this dossier as the quick reference for ownership, daily rituals, and escalation tooling.

## Subsystem Ownership

| Scope | Primary Steward | Backup Steward | Operational Artifacts |
| --- | --- | --- | --- |
| RAZAR boot sequence orchestration | Selene Voss (@selene-ops) | Malik Arroyo (@malik-runtime) | [`razar/boot_orchestrator.py`](../../razar/boot_orchestrator.py)
| Remote repair handovers & audit logging | Taryn Ibarra (@taryn-sre) | Yoshi Akari (@yoshi-integrations) | [`agents/razar/ai_invoker.py`](../../agents/razar/ai_invoker.py)
| Escalation thresholds & Prometheus exporters | Malik Arroyo (@malik-runtime) | Taryn Ibarra (@taryn-sre) | [`razar/boot_orchestrator.py`](../../razar/boot_orchestrator.py), [`docs/runbooks/razar_escalation.md`](../runbooks/razar_escalation.md)
| Release rehearsal handoffs | Selene Voss (@selene-ops) | Project release captain on rotation | [`docs/release_runbook.md`](../release_runbook.md)

### Integration Notes
- The boot orchestrator persists per-component success and runtime metrics, promotes the best-known boot sequence, and honors quarantine decisions before launching dependent services. Squad stewards must keep the [mission brief exchange](../mission_brief_exchange.md) diagrams aligned with any sequencing changes.
- `agents/razar/ai_invoker.py` resolves remote repair credentials from environment variables, records every patch suggestion to `logs/razar_ai_invocations.json`, and surfaces missing secrets as actionable errors. Updating agent rosters requires verifying both config diffs and credential hygiene.

## Daily Rituals

1. **Metrics pulse (08:45 UTC):** Review the overnight boot report exported by `razar.boot_orchestrator.finalize_metrics()` and confirm the Prometheus stream still emits `success_rate`, retry durations, and quarantine counts. Any regression below the 95% success baseline is logged for standup.
2. **Runbook alignment (09:00 UTC):** Walk through the RAZAR escalation runbook and release rehearsal checklist to ensure thresholds, notification channels, and fallback contacts match the current environment. Update `docs/runbooks/razar_escalation.md` and `docs/release_runbook.md` when new failure patterns appear.
3. **Remote agent roster sync (09:15 UTC):** Validate that `agents/razar/ai_invoker.py` can load `config/razar_ai_agents.json`, each active agent advertises a healthy endpoint, and the expected credentials resolve from the environment. Record any drift in `logs/razar_ai_invocations.json` and alert ops if an agent token rotates.
4. **Identity fingerprint audit (Release rehearsals & doctrine pushes):** Run `python scripts/refresh_crown_identity.py --use-stub` before release dry runs or after Genesis/INANNA doctrine edits to rebuild `data/identity.json`, publish the new fingerprint, and archive the refresh transcript under `logs/identity_refresh/`. Share the printed digest in the rehearsal channel so the wake-up crew tracks which imprint they exercised.【F:scripts/refresh_crown_identity.py†L1-L148】

## Reference Threads
- Follow the escalation ladder defined in [`docs/co_creation_escalation.md`](../co_creation_escalation.md) when mission briefs stall.
- Coordinate with Nazarick servant owners via [`docs/nazarick_agents.md`](../nazarick_agents.md) whenever remote agents accept a patch suggestion.
- Submit weekly findings to the Alpha v0.1 execution review so the roadmap reflects real-world reliability data.
