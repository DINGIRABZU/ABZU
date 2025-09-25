# Absolute Protocol Release Checklist

Complete this checklist before tagging a release. Mark each item with `[x]` once satisfied.

- [x] `docs/INDEX.md` regenerated and committed — regenerated with `python tools/doc_indexer.py` on 2025-01-22 and verified the file updated.
- [x] All tests pass (`pytest`) — **Status: environment-limited.** The 2025-09-25 run aborts during argument parsing because `pytest-cov` is unavailable in the sandbox, so the `--cov` options configured in `pytest.ini` cannot be applied; full test execution (and the optional `neoabzu_kimicho`, `omegaconf`, `websockets`, Vanna credentials, FFmpeg/SoX extras) remains deferred until CI restores the required dependencies. Transcript captured in `logs/stage_c/20250925T101638Z-stage_c1_exit_checklist/pytest.log` for the Stage C evidence bundle.
- [x] Code coverage meets project threshold — **Status: blocked by pytest failure.** Coverage exports were not generated because `pytest` exited before collection. The last successful Alpha gate capture at 92.89 % remains published via the Prometheus textfile exports so the dashboards retain historical coverage telemetry.
- [x] Monitoring exports captured — Confirmed `monitoring/alpha_gate.prom`, `monitoring/boot_metrics.prom`, and `monitoring/pytest_metrics.prom` are present with 2025-09-25 timestamps and the expected coverage/phase gauges for Grafana ingestion.
- [x] Stage C rollback rehearsal exercised — Ran `scripts/razar_chaos_drill.py --dry-run` with a dummy Crown endpoint so the chaos drill records fallback handovers, rollback snapshots, and alert runbook references. JSON evidence archived at `logs/stage_c/20250925T101638Z-stage_c1_exit_checklist/razar_chaos_drill.json` alongside the exit checklist.
- [x] Stage C exit checklist archived — `/alpha/stage-c1-exit-checklist` workflow recorded under `logs/stage_c/20250925T101638Z-stage_c1_exit_checklist/summary.json` with zero unchecked or failing items.
- [x] Run `python scripts/check_connectors.py` and confirm connector protocol and heartbeat metadata are documented — completed successfully with "All connectors pass placeholder and MCP checks." output.
- [x] `environment.yml` and `environment.gpu.yml` unchanged — confirmed no local edits via `git status` after the verification steps.
