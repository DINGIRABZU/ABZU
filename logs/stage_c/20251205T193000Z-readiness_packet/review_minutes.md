# Cross-team beta readiness review — minutes

- **Date:** 2025-12-08 16:00 UTC
- **Location:** Remote (Codex sandbox bridge call)
- **Facilitator:** @release-ops
- **Attendees:** @release-ops, @ops-team, @neoabzu-core, @integration-guild, @audio-lab, @qa-lead
- **Packet:** `logs/stage_c/20251205T193000Z-readiness_packet/`

## Summary
- Confirmed the sandbox bundle captures the 2025-11-05 Stage A sweeps and the 2025-12-05 Stage B ledger refresh, linking each to the `environment-limited` warnings emitted in the latest artifacts.
- Revalidated that MCP handshake and heartbeat exports remain sandbox-only, so the readiness packet keeps the "environment-limited" status blocks for `/alpha/stage-b3-connector-rotation` and `/alpha/stage-c4-operator-mcp-drill` until the gate-runner slot replays them on hardware.
- Established the hardware replay window on **2025-12-12 18:00 UTC (gate-runner-02)** to close the MCP credential gaps and regenerate telemetry hashes.

## Decisions
1. Proceed with beta readiness once the 2025-12-12 hardware replay lands; no further sandbox iterations required before that slot.
2. Tag every readiness update and PR touching the packet with the exact sandbox skip strings captured in Stage A/B/C evidence (`environment-limited: python -m build unavailable`, `environment-limited: MCP gateway offline`), mirroring the guardrails in the Absolute Protocol.
3. Publish a consolidated update to `docs/roadmap.md` and `docs/PROJECT_STATUS.md` referencing the new Stage A/B/C artifacts and the hardware replay schedule so downstream audits inherit the same context.

## Action items
| Owner | Action | Due |
| --- | --- | --- |
| @ops-team | Mirror the Stage A bootstrap, replay, and gate shakeout runs onto the gate-runner evidence ledger during the 2025-12-12 hardware slot, capturing updated coverage exports. | 2025-12-13 |
| @integration-guild | Execute `/alpha/stage-b3-connector-rotation` on hardware and upload the refreshed `stage_b_rotation_drills.jsonl` bundle with the `environment-limited` tag cleared. | 2025-12-13 |
| @neoabzu-core | Re-run `/alpha/stage-c4-operator-mcp-drill` with live credentials, attach MCP handshake/heartbeat payloads, and publish telemetry hashes into the readiness packet updates directory. | 2025-12-13 |
| @release-ops | Update doctrine summaries (roadmap, project status, Absolute Protocol) with the 2025-12 readiness review outcome and hardware follow-up cadence. | 2025-12-09 |

## Environment-limited evidence recap
- Stage A gate automation retains sandbox skips for build, health, and coverage exports until hardware replays restore FFmpeg, SoX, docker, aria2c, and `pytest-cov`. (`environment-limited: python -m build unavailable`; `environment-limited: Missing tools: docker sox ffmpeg aria2c`).
- Stage B memory proof and connector rotation depend on Neo-APSU components and MCP credentials that are stubbed in the sandbox (`environment-limited: neoabzu optional bundle unavailable`; `environment-limited: MCP gateway offline`).
- Readiness bundle `readiness_bundle.json` documents the pending MCP replay and rotation drill gaps; these must be cleared before Stage D promotion.
