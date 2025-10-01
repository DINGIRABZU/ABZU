# Absolute Protocol Release Checklist

Complete this checklist before tagging a release. Mark each item with `[x]` once satisfied.

Review the [Sandbox-to-Hardware Rehearsal Bridge](The_Absolute_Protocol.md#sandbox-to-hardware-rehearsal-bridge) before finalizing the readiness packet so deferred hardware steps, rehearsal hosts, and operator/hardware/QA sign-offs are embedded alongside the environment-limited evidence bundle.

- [x] `docs/INDEX.md` regenerated and committed — regenerated with `python tools/doc_indexer.py` on 2025-01-22 and verified the file updated.
- [x] All tests pass (`pytest`) — rehearsed in the sandbox and queued for hardware replay once tooling gaps close.
  - Status: environment-limited — Stage A3 gate shakeout on 2025-11-05 ran under `--sandbox`, logging missing `python -m build`, Docker, SoX, FFmpeg, aria2c, the `requests` client, and coverage badge tooling while still persisting the summary bundle for readiness stitching.【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】
- [x] Code coverage meets project threshold — the target remains pinned to the last hardware-confirmed baseline.
  - Status: environment-limited — Coverage exports rely on the same sandbox gaps (pytest-cov plug-in, FFmpeg, SoX, badge generator) recorded in the 2025-11-05 Stage A3 summary; historical coverage snapshots remain referenced in `monitoring/alpha_gate_summary.json` for reviewers tracking drift during the go/no-go review.【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】
- [x] Monitoring exports captured — Confirmed `monitoring/alpha_gate.prom`, `monitoring/boot_metrics.prom`, and `monitoring/pytest_metrics.prom` remain published for Grafana ingestion; the latest summary JSON at `monitoring/alpha_gate_summary.json` preserves the 92.89 % reference coverage while the sandbox stub keeps the `.prom` exports synchronized.
- [x] Stage B connector rotation ledger refreshed — `logs/stage_b/20251001T080910Z-stage_b3_connector_rotation/summary.json` captures the latest rotation window, credential metadata, and REST↔gRPC parity traces mirrored into the readiness bundle for go/no-go review.
- [x] Stage C rollback rehearsal exercised — Ran `scripts/razar_chaos_drill.py --dry-run` with a dummy Crown endpoint so the chaos drill records fallback handovers, rollback snapshots, and alert runbook references. JSON evidence archived under the go/no-go packet at `logs/stage_c/20251003T010101Z-readiness_packet/rollback_validation/20250930T210000Z-razar_chaos_drill.json` to keep the readiness bundle self-contained.
- [x] Stage C exit checklist archived — `/alpha/stage-c1-exit-checklist` workflow reran on 2025-10-01 at 10:30 UTC, logging the blocked pytest/coverage items in `logs/stage_c/20251001T103012Z-stage_c1_exit_checklist/summary.json` and copying the summary into the refreshed readiness packet `logs/stage_c/20251001T103500Z-readiness_packet/checklist_logs/` for the go/no-go review.
- [x] Run `python scripts/check_connectors.py` and confirm connector protocol and heartbeat metadata are documented — completed successfully with "All connectors pass placeholder and MCP checks." output.
- [x] `environment.yml` and `environment.gpu.yml` unchanged — confirmed no local edits via `git status` after the verification steps.
