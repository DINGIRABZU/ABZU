# Stage C Readiness Packet — 2025-12-12 hardware prep

This packet consolidates the latest Stage C evidence for stakeholders ahead of the
2025-12-12 18:00 UTC gate-runner-02 hardware replay. Share this directory when
circulating updates so reviewers can open each artifact directly from source
control.

## Artifact index
- [`readiness_bundle/readiness_bundle.json`](./readiness_bundle/readiness_bundle.json)
  – Canonical Stage A/B/C manifest copied from the 2025-10-01 packet; retains
  sandbox deferrals for MCP drills and connector rotation until hardware replays
  land.
- [`demo_assets/telemetry/summary.json`](./demo_assets/telemetry/summary.json)
  – Stage C2 scripted demo telemetry with media manifest and events log.
- [`mcp_drill/summary.json`](./mcp_drill/summary.json) plus
  [`mcp_drill/mcp_handshake.json`](./mcp_drill/mcp_handshake.json) and
  [`mcp_drill/heartbeat.json`](./mcp_drill/heartbeat.json) – Latest sandbox MCP
  drill outputs awaiting live credential replay.
- [`exit_checklist/summary.json`](./exit_checklist/summary.json) – Stage C1 exit
  checklist capturing outstanding environment-limited steps and evidence links.
- [`review_minutes.md`](./review_minutes.md) – 2025-12-08 cross-team review
  minutes documenting ownership, decisions, and sandbox constraints.

## Hardware follow-ups
- **Gate-runner parity sweep (2025-12-12 18:00 UTC):** Ops to replay the Stage A
  bootstrap, replay, and gate automation flows on hardware, clearing
  `environment-limited: python -m build unavailable` and tooling gaps noted in
  the Stage A evidence bundles.
- **Connector rotation refresh (due 2025-12-13):** Integration guild to execute
  `/alpha/stage-b3-connector-rotation` on hardware and update
  `logs/stage_b_rotation_drills.jsonl` so the readiness bundle can drop the MCP
  gateway deferral.
- **MCP drill replay (due 2025-12-13):** Neo-APSU core to re-run
  `/alpha/stage-c4-operator-mcp-drill` with production credentials, publishing
  refreshed handshake/heartbeat telemetry and hashes into the packet.
- **Doctrine sync (due 2025-12-09):** Release ops to propagate these follow-ups
  into roadmap, PROJECT_STATUS, and Absolute Protocol updates to keep doctrine
  aligned with the hardware window.

## Environment-limited notes
All artifacts remain tagged with the sandbox skip reasons captured in the Stage
A/B/C evidence (`environment-limited: python -m build unavailable`,
`environment-limited: MCP gateway offline`, `environment-limited: neoabzu
optional bundle unavailable`). Hardware reruns must attach refreshed transcripts
and telemetry hashes to close these gaps.

## Checksums
- `sha256 0ffb56ae01c4bc0672682f573962e05c796d5a53a0fc4cd37b5e26f50cb8ea97`
  – [`readiness_bundle/readiness_bundle.json`](./readiness_bundle/readiness_bundle.json)
- `sha256 7150d6e459569c5a0f57b03dc5189a5e2116ecde5a959966cad8901130b66d06`
  – [`demo_assets/telemetry/summary.json`](./demo_assets/telemetry/summary.json)
- `sha256 2ad9b4add591862446626754b86b0d1c41a74ea4c1d31199e0a7e436472a67bb`
  – [`mcp_drill/mcp_handshake.json`](./mcp_drill/mcp_handshake.json)
- `sha256 b87c14920398b44479f3aca76dc5bd752a3147beedfe8216371d5c0000351bc5`
  – [`mcp_drill/heartbeat.json`](./mcp_drill/heartbeat.json)
