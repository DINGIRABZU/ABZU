# Beta rehearsal packet template

Use this template when assembling the rehearsal packet that precedes beta GO
reviews. The template aligns with the Stage D bridge ledger, Stage E transport
snapshot, and sandbox-to-hardware guardrails described in the doctrine.
Document every environment-limited item with the exact `environment-limited:
<reason>` phrasing from readiness artifacts so auditors can trace deferred
hardware steps.【F:docs/documentation_protocol.md†L1-L40】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L200】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】

## 1. Sandbox evidence bundle

1. **Recorded transport parity exports.** Attach the JSON suites from
   `tests/fixtures/transport_parity/` and note the checksum hash enforced by the
   contract suite. These exports provide the REST↔gRPC payloads, telemetry
   metrics, and MCP rotations for `operator_api`, `operator_upload`, and
   `crown_handshake` so reviewers can diff parity without a live cluster.
   【F:tests/fixtures/transport_parity/operator_api_stage_e.json†L1-L138】【F:tests/fixtures/transport_parity/operator_upload_stage_e.json†L1-L138】【F:tests/fixtures/transport_parity/crown_handshake_stage_e.json†L1-L130】【F:tests/transport_parity/test_recorded_contracts.py†L1-L209】
2. **Readiness packet extracts.** Include the Stage C recap (`readiness_bundle`
   and MCP drill summaries) plus the Stage E transport summary so the rehearsal
   packet inherits the same evidence trails that the roadmap and status docs
   cite.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L185】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】
3. **Grafana dashboard export.** Attach the latest JSON export or screenshot of
   the `operator-transport-parity` board, noting the dashboard hash and any
   environment-limited annotations. Link back to the sandbox export section of
   the transport pilot guide so reviewers can replay the panels locally.
   【F:monitoring/operator_transport_pilot.md†L54-L105】
4. **Demo asset ledger.** Bundle the Stage C2 storyline replay artifacts and the
   corresponding evidence manifest so demo hosts can rehearse from identical
   assets during beta walkthroughs.【F:logs/stage_c/20251001T085114Z-stage_c2_demo_storyline/summary.json†L1-L78】【F:evidence_manifests/stage-c-demo-storyline.json†L1-L40】

## 2. MCP rotation and credential logbook

1. **Rotation receipts.** Copy the Stage B rotation ledger entries covering the
   operator, upload, and Crown connectors alongside the Stage C4 MCP drill
   outputs so credential windows are traceable through the beta gate.
   【F:logs/stage_b_rotation_drills.jsonl†L1-L79】【F:logs/stage_c/20251001T093206Z-stage_c4_operator_mcp_drill/summary.json†L1-L38】
2. **Sandbox rotation evidence.** Reference the `mcp_rotations` section from the
   recorded parity exports and confirm each list contains the `precheck`,
   `handover`, and `stabilize` phases. Note that the contract suite fails if a
   phase is missing, giving the rehearsal packet a deterministic verification
   hook.【F:tests/transport_parity/test_recorded_contracts.py†L147-L177】
3. **Environment-limited follow-ups.** Flag any credential or rotation tasks that
   require the hardware replay window and cite the gate-runner schedule from the
   Stage D ledger to show when the sandbox evidence will be replayed.
   【F:docs/roadmap.md†L98-L188】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】

## 3. Governance and approvals

1. **Beta readiness minutes.** Attach the latest Stage C readiness minutes,
   Stage D bridge approvals, and planned Stage E beta review agenda so the
   rehearsal packet reflects the most recent sign-offs and outstanding tasks.
   【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】
2. **Risk and mitigation register.** Summarize the open Stage E risks (heartbeat
   latency, missing parity trace uploads, telemetry schema drift) with owners,
   mitigation plans, and environment-limited tags that match the status doc.
   【F:docs/PROJECT_STATUS.md†L198-L236】
3. **Communication plan alignment.** Reference the beta launch playbook and the
   sandbox export governance note so stakeholder updates align with the
   rehearsal evidence set.【F:docs/releases/beta_launch_plan.md†L47-L111】【F:docs/PROJECT_STATUS.md†L209-L214】

## 4. Hardware-only replay placeholders

Record the tasks that must run on hardware after the rehearsal packet is
approved. Use the same checklist during the hardware window to confirm closure.

| Task | Owner | Hardware window | Evidence to capture | Status |
| --- | --- | --- | --- | --- |
| Replay Stage C parity drill on gate-runner hardware | @ops-team | 2025-11-02 09:00 UTC | Updated `summary.json`, `parity_diff.json`, dashboard hash screenshot | environment-limited: awaiting gate-runner slot |
| Emit heartbeat latency from production connectors | @integration-guild | 2025-11-02 10:00 UTC | Heartbeat payloads + latency series ingested into transport dashboard | environment-limited: sandbox exporters missing latency |
| Confirm credential rotations on hardware controllers | @neoabzu-core | 2025-11-02 11:30 UTC | Signed rotation receipts appended to Stage D/E ledgers | environment-limited: hardware controller access |

Document follow-up notes beneath the table once hardware evidence lands. When
closing the loop, update the roadmap and status docs with the refreshed hashes
and link back to this rehearsal packet so Stage F/G reviewers inherit the same
lineage.【F:docs/roadmap.md†L160-L196】【F:docs/PROJECT_STATUS.md†L198-L236】
