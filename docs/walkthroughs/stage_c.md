# Stage C Endpoint Walkthrough

## Overview

Stage C routes assemble exit checklist evidence, demo telemetry, and MCP parity artifacts ahead of the readiness review. The operator API wraps dedicated scripts, writes outputs under `logs/stage_c/`, and defers to graceful fallbacks when sandbox prerequisites are missing so reviewers still receive structured summaries.【F:operator_api.py†L2948-L3031】【F:operator_api.py†L2902-L2935】 Always reconcile results with the [Readiness Ledger](../readiness_ledger.md), which tracks the Stage C bundle, demo stub, and pending hardware follow-ups.【F:docs/readiness_ledger.md†L14-L29】

| Endpoint | Purpose |
| --- | --- |
| `POST /alpha/stage-c1-exit-checklist` | Runs `validate_absolute_protocol_checklist.py` and returns checklist status, emitting HTTP 400 only when explicit failures are logged.【F:operator_api.py†L2948-L2971】 |
| `POST /alpha/stage-c2-demo-storyline` | Invokes the scripted demo harness to capture telemetry, storing assets under `stage_c2_demo_storyline/` inside the run directory.【F:operator_api.py†L2974-L2990】 |
| `POST /alpha/stage-c3-readiness-sync` | Aggregates Stage A/B artifacts into a merged readiness snapshot, writing fallback JSON if aggregation fails so the call still completes.【F:operator_api.py†L2902-L2935】【F:operator_api.py†L2993-L3008】 |
| `POST /alpha/stage-c4-operator-mcp-drill` | Exercises the MCP adapter, attaches REST↔gRPC parity data on success, and reports environment-limited errors if credentials are absent.【F:operator_api.py†L3011-L3029】 |

## Pre-flight checklist

1. Verify the latest Stage A and Stage B summaries exist before running the readiness sync so aggregation can attach accurate slugs and artifacts.【F:operator_api.py†L1084-L1176】
2. Launch the FastAPI service and obtain a bearer token per the Stage A walkthrough.【F:server.py†L256-L276】
3. Ensure `logs/stage_c/20251205T193000Z-readiness_packet/` is mounted or writable so new runs can be compared with the existing readiness bundle and review schedule.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L37】

## Triggering the Stage C endpoints

```bash
curl -X POST "http://localhost:8000/alpha/stage-c1-exit-checklist" \
  -H "${AUTH_HEADER}"

curl -X POST "http://localhost:8000/alpha/stage-c2-demo-storyline" \
  -H "${AUTH_HEADER}"

curl -X POST "http://localhost:8000/alpha/stage-c3-readiness-sync" \
  -H "${AUTH_HEADER}"

curl -X POST "http://localhost:8000/alpha/stage-c4-operator-mcp-drill" \
  -H "${AUTH_HEADER}"
```

Capture each JSON response together with the generated directories so the readiness ledger and review minutes can confirm bundle contents.

## Expected evidence

- `logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json` — documents sandbox-only MCP artifacts, demo telemetry stub, and missing rotation drills marked as environment-limited.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L37】
- `logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md` — records the 2025-12-08 review decisions and the scheduled 2025-12-12 hardware replay window.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L33】
- `logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json` — shows `status: not-captured` with an `environment_limited` reason, signalling that the sandbox run succeeded without live credentials.【F:logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json†L1-L12】
- `logs/stage_c/20251205T193000Z-readiness_packet/demo_telemetry/summary.json` — tracks the demo telemetry stub awaiting hardware replay.【F:logs/stage_c/20251205T193000Z-readiness_packet/demo_telemetry/summary.json†L1-L4】

Reference these artifacts in the readiness ledger so reviewers can reconcile sandbox stubs with the planned gate-runner replay.【F:docs/readiness_ledger.md†L14-L29】

## Recording environment-limited notes

Follow the documentation protocol by quoting the exact `environment-limited` strings from the readiness bundle and minutes, citing the bundle directory, and tagging the hardware replay schedule in every doctrine update.【F:docs/documentation_protocol.md†L39-L68】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L24】 Note that Stage C runs should inherit Stage A/B skip strings, so include those references when updating roadmap or PROJECT_STATUS entries.

## Troubleshooting & graceful degradation

- **Aggregation failures.** If `_stage_c3_command` encounters an error, the fallback writer creates an error summary that still completes the request. Inspect the generated JSON for `status: error` and document it as environment-limited while scheduling a rerun after the blocking dependency is restored.【F:operator_api.py†L2902-L2935】
- **Missing MCP credentials.** Stage C4 surfaces a sandbox failure message and marks the handshake JSON as not captured; treat this as environment-limited evidence and coordinate with the hardware replay window instead of retrying in the sandbox.【F:operator_api.py†L3011-L3029】【F:logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/handshake.json†L1-L12】
- **Telemetry tooling unavailable.** Even without OpenTelemetry metrics, the router sets counters to `None` and the endpoints continue to run. Note the missing histograms in your environment-limited log so dashboards can be reconciled later.【F:operator_api.py†L46-L132】

## Readiness ledger linkage

Update the Stage C entries in the readiness ledger with run IDs, bundle paths, and environment-limited reasons immediately after each call. Include links to the review minutes and scheduled hardware replay date so auditors can cross-reference the sandbox evidence with forthcoming hardware captures.【F:docs/readiness_ledger.md†L14-L29】【F:logs/stage_c/20251205T193000Z-readiness_packet/review_minutes.md†L1-L33】
