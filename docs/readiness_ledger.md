# Readiness Ledger

This ledger centralizes the evidence packages that gate Stage D/G hardware
promotion: the Stage B rotation ledger, the Stage C readiness snapshot captured
on 2025-12-05, and the accompanying demo telemetry stub. Use it alongside the
Stage C review minutes when updating doctrine so sandbox deferrals stay aligned
with the hardware replay queue.

## Artifact overview

| Artifact | Path | Owner(s) | Sandbox caveat | Hardware follow-up |
| --- | --- | --- | --- | --- |
| Stage B rotation ledger | `logs/stage_b_rotation_drills.jsonl` | @neoabzu-core【F:docs/roadmap.md†L158-L169】 | `environment-limited: MCP gateway and /alpha/stage-b3-connector-rotation unavailable in Codex sandbox` | Re-run `/alpha/stage-b3-connector-rotation` on gate-runner-02 during the 2025-12-12 hardware window to refresh credential contexts and attach fresh hashes to the packet.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L8-L16】 |
| Stage C readiness snapshot (2025-12-05) | `logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json` | @release-ops【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L24-L32】 | Metadata-only merge while MCP handshake/heartbeat remain stubbed and Stage B contexts are awaiting replay.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L17-L31】 | Confirm MCP handshake/heartbeat exports and rotation ledger parity during the 2025-12-12 review; publish updated bundle hashes after hardware replay.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L8-L16】 |
| Demo telemetry stub (2025-12-05) | `logs/stage_c/20251205T193000Z-readiness_packet/demo_telemetry/summary.json` | @audio-lab · @qa-lead【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L4-L13】 | `environment-limited: Demo telemetry export deferred; awaiting sandbox-to-hardware replay window.`【F:logs/stage_c/20251205T193000Z-readiness_packet/demo_telemetry/summary.json†L1-L5】 | Capture live media/telemetry during the gate-runner session and replace the stub with signed exports in the readiness packet.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L8-L16】 |

## Sandbox caveats & linkage

- The readiness bundle explicitly tags the Stage B rotation ledger verification as
  `environment-limited`, noting the missing MCP gateway and connector rotation
  command; treat the ledger as stale until hardware replay completes.【F:logs/stage_c/20251205T193000Z-readiness_packet/readiness_bundle.json†L1-L36】
- Demo telemetry remains stubbed with an `environment-limited` status until the
  gate-runner slot captures the scripted run; the same tag must flow into change
  logs and doctrine updates.【F:logs/stage_c/20251205T193000Z-readiness_packet/demo_telemetry/summary.json†L1-L5】
- Review agenda and prerequisites for the 2025-12-08 cross-team session enumerate
  the hardware reruns (rotation ledger, MCP drill) required before clearing these
  tags—reference this schedule whenever updating roadmap or status notes.【F:logs/stage_c/20251205T193000Z-readiness_packet/review_schedule.md†L1-L16】

## Reporting expectations

1. Link roadmap and status updates directly to this ledger so reviewers can see
   which artifacts remain sandbox-bound and who owns the hardware replay.
2. Mirror the `environment-limited` wording from the evidence bundle in every
   doctrine update, matching the documentation protocol requirements.
3. Once hardware captures land, update the ledger with refreshed hashes and
   owners’ sign-offs before clearing risks from the roadmap or PROJECT_STATUS.
