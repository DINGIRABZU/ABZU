# Operator transport pilot observability

The operator transport pilot introduces a dual-stack surface for the `operator_api`
service so the Stage C rehearsal scope can compare REST and gRPC behaviour before
graduating beyond the initial connectors. The Kubernetes manifest defines the
pilot envelope via annotations, dedicated ports, and environment variables that
toggle the gRPC listener alongside the legacy REST interface.【F:deployment/api/k8s-deployment.yaml†L1-L34】

## Metrics and traces

Both transports now emit OpenTelemetry spans and metrics that capture latency,
error counts, and fallback invocations. The shared helpers in `operator_api.py`
wrap command dispatch, memory queries, and handover flows with a tracer, a
histogram (`operator_api_transport_latency_ms`), and counters for errors and
fallbacks so Grafana panels can pivot on the `transport` and `operation`
attributes.【F:operator_api.py†L54-L209】【F:operator_api.py†L214-L374】 The gRPC
handler reuses the same helpers and surfaces its own span events when it drops
into the REST fallback path, preserving the parity traces stored with the
Stage C evidence bundle.【F:operator_api_grpc.py†L1-L148】

## Dashboard layout

Create a dedicated Grafana dashboard with:

1. **Latency comparison** – a time-series panel plotting
   `operator_api_transport_latency_ms` for REST and gRPC on the same axis.
2. **Error matrix** – a table panel aggregating
   `operator_api_transport_errors_total` grouped by `operation` and `reason` so
   MCP handshake failures, permission denials, and dispatcher exceptions stay
   visible to release ops.
3. **Fallback tracker** – a single-stat panel showing the most recent
   `operator_api_transport_fallback_total` counts; annotate the panel with the
   gRPC fallback metadata key `abzu-fallback` for quick log correlation.【F:tests/test_operator_transport_contract.py†L1-L137】
4. **Span list** – a trace table filtered on
   `operator_api.grpc.dispatch_command` to confirm that REST and gRPC runs share
   the same command IDs during rehearsals.【F:operator_api_grpc.py†L16-L86】

Add Stage E panels to the same dashboard:

- **Heartbeat compliance** – a dual-axis panel plotting heartbeat emission
  counts and derived latency for the connectors targeted for Stage E rollout
  (`operator_api`, `operator_upload`, `crown_handshake`). Leave a prominent
  annotation while the latency series is empty so weekly reviews see the gap.
- **Connector coverage** – a stat panel highlighting which Stage E connectors
  have published REST↔gRPC parity traces; wire it to the contract test output so
  missing connectors automatically surface ahead of beta sign-off.

## Log correlation and contract tests

The parity tests capture both a steady-state run (proving response equivalence)
and a failure injected run (proving the fallback metadata lands in the
trailing gRPC metadata and the command still completes). Use those tests as the
contract foundation for alert thresholds and for the Stage C readiness packet
notes describing the pilot.【F:tests/test_operator_transport_contract.py†L1-L210】 The
fallback metadata and INFO/WARN log events provide the breadcrumb trail the
monitoring team can follow when the gRPC handler rolls back to REST.【F:operator_api.py†L214-L374】【F:operator_api_grpc.py†L45-L92】

## Stage E rollout checkpoints

- Stage E promotes the transport dashboard to a standing gate: contract tests
  must remain green, parity diffs stay checksum-matched, and the heartbeat panel
  must light up for every connector before Neo-APSU governance approves beta
  traffic.【F:docs/connectors/CONNECTOR_INDEX.md†L1-L86】【F:tests/test_operator_transport_contract.py†L1-L210】
- The latest evidence bundle only captures `operator_api`; keep the dashboard’s
  connector coverage panel red for `operator_upload` and `crown_handshake` until
  their REST↔gRPC traces and heartbeat telemetry arrive, and record the gap in
  the readiness and status ledgers.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/test_operator_transport_contract.py†L1-L210】
- Heartbeat payloads remain absent in the Stage C trial, so the heartbeat latency
  graph should explicitly display “data pending” until the metric lands; copy the
  annotation into risk reviews so the missing metric remains visible.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L120】【F:tests/test_operator_transport_contract.py†L1-L210】



