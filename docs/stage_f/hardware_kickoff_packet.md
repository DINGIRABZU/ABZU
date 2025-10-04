# Stage F Hardware Kickoff Packet

This packet bundles the latest readiness ledger excerpts, the Codex simulation harness specification, and the Stage F hardware replay plan so hardware owners receive a single briefing before the gate-runner soak. It mirrors Stage F goals and exit criteria from the [Stage F+ execution plan](../stage_f_plus_plan.md) and ties every checklist item back to the sandbox documentation protocol.

## Packet contents

- **Readiness ledger overview.** Summarizes the Stage B rotation ledger, Stage C readiness snapshot (2025-12-05), and demo telemetry stub along with their environment-limited caveats and required hardware follow-ups so replay owners inherit ledger context during Stage F validation. Source: [readiness_ledger.md](../readiness_ledger.md).
- **Simulation harness specification.** Collects prerequisites, module drills, and service runbooks that detail how sandbox harness outputs map to APSU migration rows and readiness ledger evidence, enabling direct traceability when the runs are replayed on hardware. Source: [simulation_harness.md](../simulation_harness.md).
- **Stage F hardware replay plan.** Outlines the Neo-APSU modules targeted for hardware confirmation, required toolchains, dataset lineage, the sandbox-to-hardware replay sequence, and role-based approval checklists to close the Stage F gate. Source: [stage_f_hardware_replay_plan.md](../stage_f_hardware_replay_plan.md).

## Readiness ledger digest

| Artifact | Sandbox status | Hardware replay expectations |
| --- | --- | --- |
| Stage B rotation ledger | Tagged `environment-limited` while MCP gateway access and `/alpha/stage-b3-connector-rotation` remain unavailable in the Codex sandbox. | Re-run the rotation command on gate-runner-02 during the reserved hardware window and publish refreshed hashes alongside the readiness packet updates. |
| Stage C readiness snapshot (2025-12-05) | Metadata-only merge that stitches sandbox evidence while MCP heartbeat exports and Stage B contexts remain pending. | Confirm handshake/heartbeat captures and rotation ledger parity during the Stage F replay, then release updated bundle hashes for doctrine synchronization. |
| Demo telemetry stub (2025-12-05) | Stubbed with an `environment-limited` marker until live media capture occurs. | Record live demo telemetry during the hardware soak and replace the stub with signed exports in the readiness packet. |

## Simulation harness specification highlights

1. Run harness drills from the repository root with documentation environment dependencies installed, writing JSON logs under `logs/simulation_harness/<module>/` for parity review.
2. Cross-reference the APSU migration matrix for each module drill to confirm fixtures, Neo bindings, and hardware deferrals while reproducing sandbox expectations (e.g., crown router, identity loader, crown decider, prompt orchestrator, state transition engine, servant model manager, emotional state, memory store, and operator MCP adapter).
3. Apply service runbooks for memory, crown, identity, and transport harnesses to mirror sandbox CLI entry points, fixtures, and expected log snippets so hardware replays can diff outputs against readiness bundle baselines.
4. Archive harness exports now to streamline Stage F hardware replays that must retire `environment-limited` skips, capture MCP heartbeat diffs, and align with the Stage F soak alignment goals.

## Hardware replay plan snapshot

1. Target Neo-APSU modules slated for hardware confirmation: `neoabzu_crown::route_decision`, `neoabzu_rag::MoGEOrchestrator`, the Neo servant bridge, `neoabzu_crown::route_inevitability`, `neoabzu_memory::MemoryBundle`, and the Neo expression pipeline, each tied to sandbox evidence rows and rotation/readiness bundles documented in the [Stage F hardware replay plan](../stage_f_hardware_replay_plan.md).
2. Provision tooling on gate-runner hosts, including the Rust toolchain, Python bridges, telemetry exporters, MCP relays, Grafana snapshot pipeline, FFmpeg, SoX, aria2c, DAW plug-ins, and pytest coverage tooling captured as sandbox limitations in the plan and supporting sandbox evidence.
3. Stage datasets by merging the Stage C readiness bundle, Stage B rotation ledger, Stage E transport readiness snapshot, MCP handshake payloads, Neo servant telemetry baselines, and inevitability transcripts referenced by the module list so hardware operators inherit full lineage.
4. Follow the sandbox-to-hardware replay sequence: package sandbox artifacts, validate tooling parity, execute the automation hook during the reserved window, capture Grafana dashboards and heartbeat diffs, and collect signed approvals from operator, hardware, and QA leads per the replay plan.

## Stage F tooling installation checklist

- [ ] Rust toolchain and Neo-APSU bridge utilities installed per the Neo-APSU onboarding guide.
- [ ] Telemetry exporters, MCP heartbeat relays, and Grafana snapshot services provisioned to match blueprint instrumentation.
- [ ] Audio/connector dependencies (FFmpeg, SoX, aria2c, DAW plug-ins) and pytest coverage tooling installed to clear sandbox `environment-limited` flags.
- [ ] Gate-runner automation hook dry-run executed with parity logs archived in the Stage F evidence bundle.

## Stage F dataset acquisition checklist

- [ ] Stage C readiness bundle (2025-12-05) synchronized to the hardware replay workspace.
- [ ] Stage B rotation ledger replay inputs replicated and access confirmed for the gate-runner slot.
- [ ] Stage E transport readiness snapshot imported with corresponding credential windows.
- [ ] MCP handshake payloads, readiness minutes, and Neo servant telemetry baselines attached for lineage verification.

## Stage F approval sign-off checklist

- [ ] Operator lead validated sandbox bundle staging, gate-runner automation dry-run, and Grafana snapshot queue; signature captured in the Stage F evidence packet.
- [ ] QA reviewer confirmed sandbox versus hardware hash comparisons, MCP heartbeat replay, and roadmap callouts for `environment-limited` skips before signing.
- [ ] Neo-APSU owner verified servant telemetry parity, inevitability trace alignment, and approvals bundle archival with signature on record.

## Handoff checklist for sandbox engineers

Before transferring this packet to hardware owners, sandbox engineers must:

- [ ] Confirm all packet sections reference the latest readiness ledger rows, simulation harness guidance, and hardware replay plan revisions (update timestamps if any source changed).
- [ ] Verify links to sandbox evidence bundles, fixtures, and Stage F tickets resolve correctly within the repository or readiness logs.
- [ ] Note any outstanding sandbox-only skips, open risks, or tooling gaps with the exact `environment-limited: <reason>` wording used in readiness bundles and roadmap callouts.
- [ ] Re-run `pre-commit` documentation checks (index refresh, onboarding references) on modified files and attach logs if failures block hardware reviewers.
- [ ] Record the verification timestamp and engineer initials in the Stage F ticket or readiness ledger comment thread prior to handoff.
