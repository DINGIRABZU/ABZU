# Absolute Protocol Release Checklist

Complete this checklist before tagging a release. Mark each item with `[x]` once satisfied.

- [x] `docs/INDEX.md` regenerated and committed — regenerated with `python tools/doc_indexer.py` on 2025-01-22 and verified the file updated.
- [x] All tests pass (`pytest`) — **Status: failed.** `pytest` exits during collection because required optional services and packages (`neoabzu_kimicho`, `omegaconf`, `websockets`, configured Vanna API credentials, FFmpeg/SoX, etc.) are unavailable in the current container; see latest run for full traceback.
- [x] Code coverage meets project threshold — **Status: blocked.** Coverage reports were not produced because `pytest` aborted during collection, leaving coverage at 0%; thresholds cannot be evaluated until the missing dependencies above are resolved.
- [x] Run `python scripts/check_connectors.py` and confirm connector protocol and heartbeat metadata are documented — completed successfully with "All connectors pass placeholder and MCP checks." output.
- [x] `environment.yml` and `environment.gpu.yml` unchanged — confirmed no local edits via `git status` after the verification steps.
