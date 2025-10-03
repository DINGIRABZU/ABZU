# Stage A Endpoint Walkthrough

## Overview

Stage A validates the Alpha gate sweep through three operator API routes. Each POST endpoint wraps a stage script, stores artifacts under `logs/stage_a/`, and appends summaries to the readiness bundle via `_attach_summary_artifacts` so auditors can locate evidence quickly.【F:operator_api.py†L2768-L2812】 Cross-check every run against the [Readiness Ledger](../readiness_ledger.md) so sandbox deferrals stay aligned with the hardware replay queue.【F:docs/readiness_ledger.md†L1-L41】

| Endpoint | Purpose |
| --- | --- |
| `POST /alpha/stage-a1-boot-telemetry` | Runs `scripts/bootstrap.py` to capture boot telemetry with sandbox overrides and records output paths in the response payload.【F:operator_api.py†L2768-L2776】 |
| `POST /alpha/stage-a2-crown-replays` | Executes `scripts/crown_capture_replays.py` to replay deterministic scenarios and attach evidence bundles.【F:operator_api.py†L2779-L2785】 |
| `POST /alpha/stage-a3-gate-shakeout` | Launches `scripts/run_alpha_gate.sh --sandbox`, normalizes warning payloads, and publishes them as `sandbox_warnings` so downstream ledgers inherit the environment limits.【F:operator_api.py†L2788-L2812】 |

## Before you run

1. Start the FastAPI service locally: `uvicorn server:app --reload --port 8000`. The app wires in the operator router and OAuth2 token endpoint so the stage routes are available.【F:server.py†L256-L276】
2. Request a bearer token by POSTing valid operator console credentials to `/token`; reuse the returned token for all stage calls.【F:server.py†L269-L276】
3. Export `AUTH_HEADER="Authorization: Bearer <token>"` so every request records a trace entry and metrics sample.

## Triggering the Stage A endpoints

```bash
# Stage A1 boot telemetry
curl -X POST "http://localhost:8000/alpha/stage-a1-boot-telemetry" \
  -H "${AUTH_HEADER}"

# Stage A2 crown replays
curl -X POST "http://localhost:8000/alpha/stage-a2-crown-replays" \
  -H "${AUTH_HEADER}"

# Stage A3 gate shakeout
curl -X POST "http://localhost:8000/alpha/stage-a3-gate-shakeout" \
  -H "${AUTH_HEADER}"
```

Successful responses include `status`, `summary`, and absolute artifact paths. Archive the JSON replies alongside `logs/stage_a/<run-id>/` so the readiness ledger can reference the exact bundle hashes.

## Expected evidence

After the sandbox sweep, confirm each summary file exists and logs the sandbox warning set instead of failing outright:

- `logs/stage_a/20251105T170000Z-stage_a1_boot_telemetry/summary.json` — notes missing `python -m build`, Docker, SoX, FFmpeg, aria2c, and `pytest-cov`, while marking the run `environment-limited` rather than aborting.【F:logs/stage_a/latest/stage_a1_boot_telemetry-summary.json†L1-L29】
- `logs/stage_a/20251105T171000Z-stage_a2_crown_replays/summary.json` — records deterministic replay outputs and lists audio tooling gaps as environment-limited warnings.【F:logs/stage_a/latest/stage_a2_crown_replays-summary.json†L1-L24】
- `logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json` — captures skipped build/health/test phases with structured reasons so Stage C reviewers can mirror the same skip strings.【F:logs/stage_a/latest/stage_a3_gate_shakeout-summary.json†L1-L28】

Attach these summaries to the readiness ledger entry for Stage A evidence and hyperlink the corresponding bundle ID when updating roadmap or status pages.【F:docs/readiness_ledger.md†L14-L41】

## Recording environment-limited notes

Use the exact `environment-limited: <reason>` phrasing from the summaries whenever you document the run. The documentation protocol requires quoting the skip reasons, referencing the readiness packet location, and tagging the supporting minutes so hardware owners inherit the same replay plan.【F:docs/documentation_protocol.md†L39-L68】 Add the note to the ledger item and to any doctrine update that references the Stage A sweep.

## Troubleshooting & graceful degradation

- **Missing tooling (python -m build, Docker, FFmpeg, SoX, aria2c, pytest-cov).** The stage scripts emit `environment-limited` warnings and continue; verify the summary files list each missing binary rather than failing the request.【F:logs/stage_a/latest/stage_a1_boot_telemetry-summary.json†L1-L29】【F:logs/stage_a/latest/stage_a3_gate_shakeout-summary.json†L1-L28】
- **Multipart uploads disabled.** If `python-multipart` is absent, `_HAS_MULTIPART` is set to `False`, but Stage A endpoints remain available because they do not rely on file uploads.【F:operator_api.py†L39-L77】 Keep the warning in the environment-limited notes and proceed.
- **Metrics backend offline.** When OpenTelemetry metrics are unavailable, the router falls back to `None` counters and still serves the stage routes, so runs record successfully albeit without latency histograms.【F:operator_api.py†L46-L132】 Document the lack of metrics as an environment-limited observation if you depend on stage latency dashboards.

## Readiness ledger linkage

After each run, append the JSON response and artifact hash to the Stage A section of the readiness ledger so hardware reviewers can reconcile sandbox skips with the pending gate-runner replay.【F:docs/readiness_ledger.md†L14-L41】 Include the run ID and environment-limited reason in the ledger note to maintain parity with the readiness packet.【F:docs/documentation_protocol.md†L39-L68】
