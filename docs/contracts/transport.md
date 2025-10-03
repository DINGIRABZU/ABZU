# Transport Module Contract

## Overview
The transport contract covers parity between REST and gRPC operator surfaces plus the recorded Stage C/Stage E artifacts that prove checksum stability. It outlines how command payloads travel through the REST router, how the gRPC service mirrors results (with REST fallback), and what evidence bundles must accompany beta and hardware reviews.

## Sample Inputs and Outputs
- **Command parity.** Posting `{"operator": "crown", "agent": "razar", "command": "status"}` to `/operator/command` returns `{ "result": {"ack": "status"}, "command_id": ... }`, and the gRPC `_dispatch_command` yields the same structure for the same payload.【F:tests/test_operator_transport_contract.py†L150-L175】
- **Fallback metadata.** When the first gRPC dispatch raises `RuntimeError("grpc failure")`, enabling `enable_rest_fallback` causes the second attempt to call REST and set trailing metadata `("abzu-fallback", "rest")`, proving the fallback hook works.【F:tests/test_operator_transport_contract.py†L178-L206】
- **Stage C bundle format.** Trial entries expose `rest_path`, `grpc_path`, and `diff_path` fields whose JSON payloads must produce identical normalized handshakes and checksums, with diff artifacts asserting `parity=True` and empty `differences` arrays.【F:tests/test_operator_transport_contract.py†L209-L239】
- **Stage E readiness snapshot.** The latest readiness summary enumerates connectors (`operator_api`, `operator_upload`, `crown_handshake`), parity booleans, checksum hashes, telemetry hashes, and artifact paths that must exist on disk for each connector.【F:tests/test_operator_transport_contract.py†L241-L273】 Sample payloads live under `tests/fixtures/transport_parity/`, capturing both legacy and Neo revisions plus telemetry spans.【F:tests/fixtures/transport_parity/operator_api_stage_e.json†L1-L148】

## Expected Logging and Telemetry
- Stage E summaries should list `heartbeat_missing`, `rest_latency_missing`, and `grpc_latency_missing` gap tags whenever sandbox runs lack hardware metrics, alongside a dashboard URL for reviewers to track remediation.【F:tests/test_operator_transport_contract.py†L275-L303】
- Automation should emit `EnvironmentLimitedWarning` from `_stage_runtime` when FFmpeg/SoX or native Neo‑APSU modules are absent; keep these warnings in the transport evidence bundle so reviewers know why heartbeat metrics remain stubbed.【F:scripts/_stage_runtime.py†L27-L63】

## Failure Modes and Recovery
- **Missing artifacts.** If any Stage C handshake file is absent or unreadable, `_load_stage_c_trial_entries` drops the entry, causing the contract test to fail with `"expected Stage C transport parity artifacts"`. Mirror this check when validating new exports.【F:tests/test_operator_transport_contract.py†L29-L71】【F:tests/test_operator_transport_contract.py†L209-L213】
- **Checksum drift.** Mismatched checksums or diff payloads will trip the assertions that parity is `True` and the checksum fields align; recompute bundles with `compute_handshake_checksum` before publishing readiness packets.【F:tests/test_operator_transport_contract.py†L229-L239】
- **Heartbeat telemetry gaps.** Stage E summaries deliberately mark missing heartbeat and latency metrics. Until hardware spans are captured, leave the gaps visible and document them as environment-limited skips in roadmap and PROJECT_STATUS updates.【F:tests/test_operator_transport_contract.py†L275-L303】

## Reusable Fixtures and Stubs
- Recorded Stage E connector exchanges (`operator_api_stage_e.json`, `operator_upload_stage_e.json`, `crown_handshake_stage_e.json`) provide canonical payloads and telemetry hashes for transport contract tests.【F:tests/fixtures/transport_parity/operator_api_stage_e.json†L1-L148】
- The `_DummyContext` class in the contract tests is the minimal gRPC context stub; reuse it when exercising metadata flows or fallback behaviour in new tests.【F:tests/test_operator_transport_contract.py†L112-L148】
- Call `_stage_runtime.bootstrap()` before running integration scripts so the same sandbox overrides (including `INANNA_AI.glm_integration` and Crown modules) are active when transport exercises cross-module calls.【F:scripts/_stage_runtime.py†L27-L108】

## Future Work
Stage E roadmap checkpoints require attaching REST↔gRPC contract results, Grafana dashboard hashes, and Stage C bundle references to beta reviews, then replaying the same artifacts on gate-runner hardware during Stage G parity drills.【F:docs/roadmap.md†L170-L218】 Continue exporting heartbeat telemetry once hardware spans land, updating readiness packets and dashboards so the transport contract tracks the closure of sandbox gaps ahead of GA sign-off.【F:docs/roadmap.md†L209-L218】 Document every environment-limited warning from `_stage_runtime` alongside transport evidence until FFmpeg/SoX and Neo‑APSU binaries can be exercised outside the sandbox.【F:scripts/_stage_runtime.py†L27-L63】
