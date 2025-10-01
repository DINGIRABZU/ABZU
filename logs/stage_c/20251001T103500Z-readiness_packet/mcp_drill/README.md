# Stage C4 MCP Drill — 2025-10-01 Snapshot

The MCP drill replayed at 10:33 UTC on 2025-10-01 using the sandbox stub
adapter to capture handshake and heartbeat payloads without external
connectivity. The copied artifacts anchor the credential window that feeds
Stage B rotation ledgers and the readiness bundle.

- `index.json` — pointer to the Stage C4 run summary and handshake/heartbeat
  evidence at `logs/stage_c/20251001T103349Z-stage_c4_operator_mcp_drill/`.
- `rotation_metadata.json`, `credential_window.json` — copied into the
  packet for quick reference alongside the readiness bundle.

Use these files to align Stage B/C credential windows during the go/no-go
review.
