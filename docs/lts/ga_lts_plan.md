# GA Long-Term Support Plan

The GA long-term support (LTS) plan anchors the maintenance cadence, doctrine
ownership, and rollback governance for the stable release. Reference this file
whenever scheduling post-GA workstreams or auditing hardware parity results.

## Doctrine anchors

- **Primary doctrine owners:** @ops-team, @qa-alliance, and @neoabzu-core. These
  groups steward the doctrine updates outlined in
  [`docs/doctrine_index.md`](../doctrine_index.md) and ensure hashes are refreshed
  when LTS checkpoints change.
- **Reference bundles:** Every LTS review must cite the Stage G bridge bundles in
  `logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/` and
  `logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/` alongside the GA
  hardware telemetry snapshot exported to
  `logs/stage_h/20251115T090000Z-ga_hardware_cutover/`.
- **Blueprint linkage:** Align updates across
  [`docs/system_blueprint.md`](../system_blueprint.md),
  [`docs/blueprint_spine.md`](../blueprint_spine.md), and the readiness chapter in
  [`docs/releases/ga_readiness.md`](../releases/ga_readiness.md) before closing an
  LTS review.

## Maintenance cadence

| Window | Scope | Required artifacts |
| --- | --- | --- |
| Quarterly (12 weeks) | Apply minor upgrades, dependency refreshes, and telemetry schema updates. | Updated roadmap entry in [`docs/roadmap.md`](../roadmap.md#maintenance), new parity hash in `logs/stage_h/<run_id>/parity_diff.json`, and signed checklist in `logs/stage_h/<run_id>/approvals.yaml`. |
| Semi-annual | Conduct infrastructure hardening, disaster recovery drills, and cost/performance audits. | Incident response post-mortems, Grafana snapshot exports, and doctrine index hash updates referencing the revised bundles. |
| Annual | Revalidate support SLAs, confirm rollback rehearsals, and renew deprecation schedules. | Consolidated GA review minutes archived under `logs/stage_h/<year>/annual_review/` with signatures from all doctrine owners. |

All cadence reviews must log outcomes in `docs/PROJECT_STATUS.md#stage-g` so the
sandbox-to-hardware bridge remains synchronized with production decisions.

## Production-grade runbooks

### Monitoring and alerting

- LTS thresholds for mission-critical surfaces are defined in
  [`monitoring/README.md`](../../monitoring/README.md#production-lts-thresholds).
  Update the Prometheus rules in `monitoring/alerts/` whenever these values
  change and archive the diff in `logs/stage_h/<run_id>/alert_rules.json`.
- Grafana dashboards referenced in the Stage E transport pilot must be snapshot
  and versioned after each quarterly review. Store exported JSON under
  `logs/stage_h/<run_id>/grafana_snapshots/` with checksum references captured in
  [`docs/doctrine_index.md`](../doctrine_index.md).

### Incident response

- Incident commanders follow the GA incident response loop documented in
  [`monitoring/README.md`](../../monitoring/README.md#ga-incident-response).
- Every page includes the latest hardware telemetry from
  `logs/stage_h/20251115T090000Z-ga_hardware_cutover/summary.json` and Stage G
  parity diffs. Archive the combined packet in
  `logs/stage_h/<incident_id>/evidence/` for post-mortems.

### Rollback governance

1. Verify sandbox stability using the rehearsal script outputs in
   `logs/stage_h/20251115T090000Z-ga_hardware_cutover/rehearsal_diff.json`.
2. Compare the production hashes against the Stage G parity bundles before
   triggering rollback. Document any delta in
   `logs/stage_h/<incident_id>/rollback_diff.json`.
3. Notify doctrine owners and update [`CHANGELOG.md`](../../CHANGELOG.md#100---2025-11-15)
   with the remediation summary within 24 hours.

The doctrine ledger in [`docs/doctrine_index.md`](../doctrine_index.md) must be
updated after each rollback rehearsal or live rollback to capture new bundle
hashes and timestamps.
