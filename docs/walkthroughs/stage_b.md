# Stage B Endpoint Walkthrough

## Overview

Stage B endpoints exercise memory load, sonic rehearsal, and connector rotation evidence. Each POST route orchestrates a script, extracts metrics, and enforces HTTP 500 responses only when the script fails; sandbox stubs instead surface `environment-limited` warnings so runs degrade gracefully.【F:operator_api.py†L2815-L2879】 Sync every invocation with the [Readiness Ledger](../readiness_ledger.md) to keep the Stage B rotation ledger and rehearsal packets traceable for hardware follow-up.【F:docs/readiness_ledger.md†L14-L32】

| Endpoint | Purpose |
| --- | --- |
| `POST /alpha/stage-b1-memory-proof` | Runs `scripts/memory_load_proof.py` against `data/vector_memory_scaling/corpus.jsonl`, attaching latency metrics and stub reasons if Neo-APSU bundles are offline.【F:operator_api.py†L2815-L2838】 |
| `POST /alpha/stage-b2-sonic-rehearsal` | Generates `stage_b_rehearsal_packet.json` with connector capability and dropout data for the rehearsal context.【F:operator_api.py†L2841-L2861】 |
| `POST /alpha/stage-b3-connector-rotation` | Executes `scripts/stage_b_smoke.py --json`, capturing rotation ledger snapshots plus REST↔gRPC parity traces.【F:operator_api.py†L2864-L2882】 |

## Pre-flight checklist

1. Ensure Stage A summaries referenced by the readiness aggregate exist so Stage B runs can link to the most recent Stage A evidence when aggregated later.【F:operator_api.py†L1084-L1176】
2. Start the FastAPI service and obtain a bearer token as described in the Stage A walkthrough; Stage B routes share the same authentication model.【F:server.py†L256-L276】
3. Export `AUTH_HEADER` and confirm `data/vector_memory_scaling/corpus.jsonl` is present; otherwise the memory proof will fail before the sandbox stubs can engage.

## Triggering the Stage B endpoints

```bash
# Memory proof
curl -X POST "http://localhost:8000/alpha/stage-b1-memory-proof" \
  -H "${AUTH_HEADER}"

# Sonic rehearsal packet
curl -X POST "http://localhost:8000/alpha/stage-b2-sonic-rehearsal" \
  -H "${AUTH_HEADER}"

# Connector rotation drill
curl -X POST "http://localhost:8000/alpha/stage-b3-connector-rotation" \
  -H "${AUTH_HEADER}"
```

Archive each JSON response next to the corresponding `logs/stage_b/<run-id>/` directory so readiness reviews can cross-check metrics, rotation snapshots, and parity traces.

## Expected evidence

- `logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json` — confirms success while flagging the Neo-APSU bundle stub and sandbox overrides, including latency percentiles and fallback reasons.【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L63】
- `logs/stage_b/20251001T214349Z-stage_b2_sonic_rehearsal/summary.json` — points to the generated rehearsal packet and captures connector capability metadata with zero dropouts.【F:logs/stage_b/20251001T214349Z-stage_b2_sonic_rehearsal/summary.json†L1-L45】
- `logs/stage_b/20251001T080910Z-stage_b3_connector_rotation/summary.json` — records REST and gRPC handshake traces, rotation window metadata, and sandbox stub warnings for missing Neo-APSU services.【F:logs/stage_b/20251001T080910Z-stage_b3_connector_rotation/summary.json†L1-L75】

Link these paths when updating the ledger’s Stage B rotation entry so reviewers can reconcile sandbox warnings with the pending hardware replay schedule.【F:docs/readiness_ledger.md†L14-L32】

## Recording environment-limited notes

Mirror the environment-limited wording from the summaries (e.g., `neoabzu_memory: optional bundle shim activated`, `MCP gateway offline`) in both the readiness ledger and doctrine updates. The documentation protocol mandates quoting the skip strings, citing the readiness packet (`logs/stage_c/20251205T193000Z-readiness_packet/`), and referencing the review minutes that plan the hardware rerun.【F:docs/documentation_protocol.md†L39-L68】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L33】

## Troubleshooting & graceful degradation

- **Neo-APSU bundle unavailable.** The memory proof summary sets `stubbed_bundle` and `runtime_stubbed` to `true` while still returning HTTP 200; surface this as an environment-limited note rather than treating it as a failure.【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L20-L63】
- **Connector rotation without MCP gateway.** When rotation evidence relies on Stage C MCP artifacts, the summary still records normalized traces but references sandbox handshake placeholders; document the missing handshake in the ledger and in readiness notes instead of rerunning in the sandbox.【F:logs/stage_b/20251001T080910Z-stage_b3_connector_rotation/summary.json†L47-L75】【F:logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json†L1-L12】
- **Optional telemetry tooling missing.** If OpenTelemetry metrics are disabled, Stage B routes proceed because counters default to `None`; capture the absence of histograms as an environment-limited observation if latency dashboards are required.【F:operator_api.py†L46-L132】

## Readiness ledger linkage

Update the Stage B rows in the readiness ledger with run IDs, artifact paths, and environment-limited reasons immediately after execution. Include references to the rehearsal packet and rotation drills so the hardware replay window documented in the review minutes can reconcile sandbox stubs with upcoming evidence updates.【F:docs/readiness_ledger.md†L14-L32】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L24】
