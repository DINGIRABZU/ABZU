# General Availability Readiness Handbook

The GA handbook consolidates service guarantees, release governance, and doctrine
links required for the production launch. Pair this chapter with the
architecture overview in [`docs/system_blueprint.md`](../system_blueprint.md),
the subsystem lineage in [`docs/blueprint_spine.md`](../blueprint_spine.md), and
the component topology captured in [`docs/ABZU_blueprint.md`](../ABZU_blueprint.md)
when validating operational coverage.

## Support service-level agreements

| Surface | Availability target | Response expectation | Escalation path |
| --- | --- | --- | --- |
| Mission-critical APIs (`operator_api`, `operator_upload`, `crown_handshake`) | 99.5% rolling 30-day availability | First triage within 15 minutes via `#ops-ga-bridge`; production fix or rollback within 2 hours. | Follow the sandbox-to-hardware bridge described in [`docs/The_Absolute_Protocol.md`](../The_Absolute_Protocol.md#stage-gate-alignment) with sign-off from operator, hardware, and QA leads. |
| Creative synthesis surfaces (`bana`, `avatar_stream`) | 99.0% rolling 30-day availability | Initial acknowledgement within 30 minutes; mitigation plan within 4 hours. | Route incidents through the avatar response playbook in [`monitoring/README.md`](../../monitoring/README.md#ga-incident-response) and attach telemetry artifacts from `logs/stage_h/`. |
| Narrative and memory stores (`memory_store`, `spiral_memory`) | 99.3% rolling 30-day availability | Triage within 30 minutes; patch or failover within 6 hours. | Invoke the rollback routine documented in [`docs/lts/ga_lts_plan.md`](../lts/ga_lts_plan.md#rollback-governance) after comparing hashes recorded in the readiness bundle. |

All incidents must capture the hardware telemetry snapshot exported to
`logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json` before the
post-mortem is filed. The checksum table in [`docs/doctrine_index.md`](../doctrine_index.md)
tracks the authoritative bundle path for auditors.

## Upgrade cadence and change management

- **Quarterly GA refresh:** Promote minor releases every 12 weeks. Coordinate
  subsystem sequencing using the Stage G bridge ledger in
  [`docs/roadmap.md`](../roadmap.md#stage-g-sandbox-to-hardware-bridge-validation).
- **Hotfix window:** Critical patches may ship out-of-cycle if the operator,
  hardware, and QA leads approve the sandbox rehearsal captured in
  `logs/stage_h/20251115T090000Z-ga_hardware_cutover/rehearsal_diff.json`.
- **Blueprint synchronization:** Every upgrade must reconcile dependency and
  topology diffs across [`docs/system_blueprint.md`](../system_blueprint.md),
  [`docs/blueprint_spine.md`](../blueprint_spine.md), and the connector catalog
  in [`docs/component_index.md`](../component_index.md). Update
  [`docs/INDEX.md`](../INDEX.md) and rerun doctrine validation scripts after each
  promotion.

## Deprecation policy

1. **Announcement:** Document upcoming removals in
   [`CHANGELOG.md`](../../CHANGELOG.md) and [`docs/roadmap.md`](../roadmap.md#maintenance)
   at least two releases before the removal lands.
2. **Compatibility windows:** Maintain compatibility shims for a minimum of one
   quarterly cycle. Log shim telemetry under `logs/stage_h/compatibility/` with
   references from the doctrine index to keep auditors informed.
3. **Rollout checkpoints:** Every deprecation requires a dry run across the
   sandbox, Stage G hardware bridge, and the GA hardware window. Capture the
   parity diffs under `logs/stage_h/<run_id>/parity_diff.json` and archive
   rollback drills according to
   [`docs/lts/ga_lts_plan.md`](../lts/ga_lts_plan.md#rollback-governance).

## Operator readiness checklist

- Confirm alert thresholds match the LTS bars in
  [`monitoring/README.md`](../../monitoring/README.md#production-lts-thresholds).
- Verify incident response and rollback rehearsals reference the GA
  hardware telemetry snapshot in `logs/stage_h/` and the Stage G bridge bundle.
- Ensure governance notes in [`docs/lts/ga_lts_plan.md`](../lts/ga_lts_plan.md)
  cite the correct doctrine owners and maintenance cadences.
- Sync blueprint references across `system_blueprint.md`, `blueprint_spine.md`,
  and `ABZU_blueprint.md` to guarantee contributors inherit the same topology
  view when planning hotfixes and upgrades.

Once these checks are green, update [`docs/roadmap.md`](../roadmap.md#general-availability)
and [`CHANGELOG.md`](../../CHANGELOG.md#100---2025-11-15) before tagging the GA
release.
