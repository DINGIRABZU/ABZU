# Beta Launch Playbook

Stage E parity enforcement and transport readiness provide the baseline for widening
access during the beta window. This playbook curates that evidence, maps security
and performance guardrails to the roadmap’s beta goals, and defines the review
rituals we will follow until general availability.

## Anchor evidence and telemetry

- **Transport parity evidence.** Link all beta decisions to the Stage E
  transport readiness bundle (`logs/stage_e/20250930T121727Z-stage_e_transport_readiness/`).
  The summary captures checksum-matched REST↔gRPC traces for `operator_api`,
  `operator_upload`, and `crown_handshake`, plus the shared telemetry hash and
  heartbeat gaps that remain environment-limited until hardware rehearsals land
  latency signals.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L63】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L64-L87】
- **Roadmap alignment.** The roadmap defines the beta milestone as the phase
  where external feedback is incorporated while hardening performance and
  security layers. Treat every checklist review as validation that those
  objectives remain on track.【F:docs/roadmap.md†L9-L18】
- **Continuous dashboards.** Keep the Grafana Stage E transport board pinned in
  weekly reviews so latency, error, heartbeat, and satisfaction panels reflect
  the latest exporter data emitted during beta rehearsals.【F:monitoring/operator_transport_pilot.md†L1-L84】

## Beta launch checklist

| Checklist Item | Owner | Evidence Path | Beta Guardrail | Status |
| --- | --- | --- | --- | --- |
| Transport parity suite green across connectors | @ops-team | `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/` | REST↔gRPC traces checksum match (`30b2c06c4b4ffeb5d403c63fb7a4ee283f9f8f109b3484876fe09d7ec6de56c8`) before any external traffic expansion. | 🔄 Ongoing |
| Heartbeat latency landing in dashboards | @integration-guild | `monitoring/grafana-dashboard.json` Stage E panels | Beta entry blocked until heartbeat latency no longer flagged as missing in Stage E summary. | ⚠️ Environment-limited |
| External feedback exporter publishing latency + satisfaction metrics | @monitoring-guild | `logs/stage_f/exporters/latest.prom` | Beta reviews require fresh latency/error-budget/satisfaction signals each week. | ✅ Initial run captured |
| Security hardening sign-offs recorded | @release-ops | `docs/releases/beta_launch_plan.md` + readiness minutes | Beta access contingent on Stage D bridge approvals and connector credential attestations. | 🔄 Pending signatures |
| Weekly feedback synthesis circulated | @release-ops | `docs/PROJECT_STATUS.md#beta-feedback-tracking` | Feedback themes and satisfaction scores shared with product + ops each review. | 🔄 In progress |

## Security guardrails

1. **Connector governance.** Beta connectors (`operator_api`, `operator_upload`,
   `crown_handshake`) retain Stage D bridge fingerprints and Stage E parity
   checksums; no rollout occurs without matching hashes and credential rotation
   proof in the readiness minutes.【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L20-L52】【F:docs/roadmap.md†L196-L247】
2. **Credential reviews.** Weekly beta reviews must confirm that credential
   rotation windows logged in Stage C readiness packets remain within validity
   and that any escalations are mirrored in the doctrine ledger before access is
   widened.【F:docs/roadmap.md†L196-L247】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L1-L44】
3. **Alert routing.** Prometheus alert rules (`monitoring/alerts/beta_feedback.yml`)
   dispatch `beta_feedback_latency_regression` and
   `beta_feedback_satisfaction_drop` notifications via the existing escalation
  notifier whenever latency exceeds the weekly threshold or satisfaction falls
  below the agreed baseline. Do not silence these alerts without documenting
  compensating controls in the risk register.【F:monitoring/alerts/beta_feedback.yml†L1-L43】【F:monitoring/escalation_notifier.py†L1-L73】

## Performance guardrails

1. **Latency compliance.** Monitor `beta_feedback_latency_ms` histograms for
   each external channel. Beta SLOs require p95 ≤ 250 ms; the dashboard panel
   derives this via histogram quantiles so breaches auto-surface in alerts and
   the weekly status table.【F:monitoring/grafana-dashboard.json†L212-L248】【F:monitoring/alerts/beta_feedback.yml†L4-L26】
2. **Error-budget tracking.** Keep the `beta_feedback_error_budget_ratio`
   gauges above 0.85. When the ratio dips, the alert rule flips to warning and
   Stage F exporter snapshots must note mitigation steps before the next review.
   【F:logs/stage_f/exporters/latest.prom†L1-L33】【F:monitoring/alerts/beta_feedback.yml†L17-L28】
3. **Satisfaction signals.** Maintain `beta_feedback_satisfaction_score`
   averages at or above the target per channel (CSAT ≥ 4.2, NPS ≥ 40). Dropoffs
   trigger the satisfaction alert and must be paired with customer notes in the
   feedback tracker.【F:logs/stage_f/exporters/latest.prom†L34-L39】【F:monitoring/grafana-dashboard.json†L240-L248】

## Weekly beta review agenda

1. Re-run contract tests and sync dashboards before the meeting; attach the
   exporter snapshot under `logs/stage_f/<timestamp>-beta_feedback/` to the
   status email.
2. Walk the checklist table above, capturing updates or blockers directly in
   `docs/PROJECT_STATUS.md`.
3. Review open alerts from `beta_feedback_latency_regression` and
   `beta_feedback_satisfaction_drop`, confirming owner, remediation plan, and
   ETA.
4. Log external feedback themes alongside the latest satisfaction scores and
   associated telemetry hash for traceability.

## Exit criteria for beta

- All checklist items marked ✅ for two consecutive weekly reviews.
- No open `critical` alerts from `beta_feedback_latency_regression` or
  `beta_feedback_satisfaction_drop` for 14 days.
- Stage F exporter snapshots show stable latency/error/satisfaction metrics and
  are archived with the doctrine ledger prior to GA planning.

Once these criteria are met, schedule the GA readiness review and merge the beta
notes into the GA playbook.
