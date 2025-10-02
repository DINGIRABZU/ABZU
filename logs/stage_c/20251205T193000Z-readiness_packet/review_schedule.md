# Cross-team beta readiness review

- **Target window:** 2025-12-08 16:00 UTC (remote)
- **Calendar status:** Invites accepted by @release-ops, @ops-team, @neoabzu-core, @integration-guild, @audio-lab, and @qa-lead on 2025-12-06 09:00 UTC; prep deck attached to the event notes.
- **Facilitator:** @release-ops
- **Agenda:**
  1. Review Stage B rotation ledger context entries (`stage-b-rehearsal`, `stage-c-prep`) and confirm the 20251205T160210Z rotation window remains tagged `environment-limited: MCP gateway offline`.
  2. Confirm MCP drill replay plan and telemetry exports, including the sandbox handshake/heartbeat artifacts at `logs/stage_c/20251205T193000Z-readiness_packet/mcp_artifacts/`.
  3. Capture environment-limited follow-ups for the hardware slot and align skip strings with [The Absolute Protocol](../../../docs/The_Absolute_Protocol.md#tagging-environment-limited-evidence).
- **Prerequisites:** Hardware rerun of `/alpha/stage-b3-connector-rotation` and `/alpha/stage-c4-operator-mcp-drill` with live MCP credentials on gate-runner-02 during the 2025-12-12 18:00 UTC window.
- **Notes:** Update `docs/roadmap.md` and `docs/PROJECT_STATUS.md` after review with hardware confirmations and cite the `environment-limited` evidence captured in Stage A/B/C artifacts so auditors inherit the sandbox context.
