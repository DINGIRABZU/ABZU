# Stage F Hardware Replay Plan

Stage F hardens Neo-APSU adoption by replaying sandbox evidence on gate-runner
hardware before the soak completes. The plan below enumerates the required
hardware validations, prerequisites, and approval flow that connects sandbox
runs to signed hardware outcomes.

## Modules requiring hardware validation

Stage F focuses on the Neo-APSU surfaces that already demonstrated sandbox
parity during Stages C–E but still need live hardware confirmation. Each module
must replay its sandbox evidence bundle on the assigned hardware runner and
capture matching hashes, rollback transcripts, and approvals:

- **`neoabzu_crown::route_decision` (Rust replacement for `crown_decider.py`).**
  Stage F replays the Stage B rotation windows and Stage C readiness bundle on
  hardware to prove deterministic routing before widening access beyond the
  sandbox parity logs.【F:docs/roadmap.md†L164-L174】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L120-L195】
- **`neoabzu_rag::MoGEOrchestrator` (Rust replacement for
  `crown_prompt_orchestrator.py`).** Hardware runs must mirror the REST↔gRPC
  handshake diffs captured during Stage C/E trials so the orchestrator parity
  ledger inherits the same checksum lineage recorded in sandbox bundles.【F:docs/roadmap.md†L165-L176】【F:logs/stage_c/20251031T000000Z-test/rest_grpc_handshake_diff.json†L1-L12】
- **`neoabzu_crown` servant bridge (replacement for
  `servant_model_manager.py`).** Stage F verifies registry callbacks and
  invocation telemetry against the sandbox traces exported in the Stage C
  readiness packet to prove the servant lifecycle is hardware-ready.【F:docs/roadmap.md†L167-L178】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L48-L120】
- **`neoabzu_crown::route_inevitability` (replacement for
  `state_transition_engine.py`).** Hardware parity captures inevitability spans
  while referencing the sandbox transcripts logged during Stage C rehearsals to
  confirm Chakra transitions remain deterministic.【F:docs/roadmap.md†L168-L180】【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L121-L185】
- **`neoabzu_memory::MemoryBundle` (replacement for `memory_store.py`).**
  Hardware replays must validate checksum parity for all eight memory layers,
  leveraging the sandbox baselines preserved in the Stage B and Stage C
  evidence bundles.【F:docs/roadmap.md†L169-L181】【F:logs/stage_b/latest/readiness_index.json†L1-L47】
- **Neo-APSU expression pipeline (replacement for `emotional_state.py`).** Stage F
  signs off aura telemetry on hardware by comparing the sandbox shim output
  documented during Stage C readiness with live sensor metrics captured during
  the replay window.【F:docs/roadmap.md†L170-L182】【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L50】

## Tooling prerequisites

- **Compiler and bridge parity.** Gate-runner hosts must expose the Rust
  toolchain, Python bridge utilities, and build prerequisites enumerated in the
  Neo-APSU onboarding guide so hardware parity binaries match the sandbox
  builds.【F:NEOABZU/docs/onboarding.md†L1-L36】
- **Blueprint host services.** Provision telemetry exporters, MCP heartbeat
  relays, and the Grafana snapshot pipeline described in the system blueprint so
  hardware captures mirror sandbox instrumentation when the replay executes.【F:docs/system_blueprint.md†L612-L667】
- **Audio/connector dependencies.** Install FFmpeg, SoX, aria2c, DAW plug-ins,
  and pytest coverage tooling flagged as environment-limited during sandbox
  rehearsals so the hardware run clears every deferred warning before
  sign-off.【F:docs/documentation_protocol.md†L31-L52】【F:logs/stage_a/20251105T172000Z-stage_a3_gate_shakeout/summary.json†L1-L53】【F:logs/stage_b/20251205T142355Z-stage_b1_memory_proof/summary.json†L1-L63】

## Dataset and evidence requirements

- **Sandbox evidence bundles.** Stage F runs start from the merged Stage C
  readiness bundle, Stage B rotation ledger, and Stage E transport readiness
  snapshot so every hardware replay references canonical sandbox artifacts and
  credential windows.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_b_rotation_drills.jsonl†L12-L115】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】
- **MCP handshake lineage.** Attach the handshake payloads and readiness
  minutes from the Stage C packet so hardware reviewers can trace queue
  ownership and confirm the replay window matches the recorded approvals.【F:logs/stage_c/20251001T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】【F:logs/stage_c/20251001T010101Z-readiness_packet/review_minutes.md†L14-L44】
- **Neo-APSU module baselines.** Archive the most recent Neo-APSU servant
  telemetry exports and route inevitability transcripts referenced by the Stage F
  module list so comparisons on hardware are hash-aligned.【F:logs/stage_c/20251031T000000Z-test/summary.json†L1-L50】【F:logs/stage_c/20251001T010101Z-readiness_packet/checklist_logs/README.md†L1-L16】

## Scheduled hardware window

Reserve gate-runner execution slots aligned to the Stage C exit checklist and
readiness minutes so the sandbox-to-hardware bridge meets The Absolute
Protocol handoff requirements.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】【F:docs/The_Absolute_Protocol.md†L54-L114】 Document the reservation ID and
ops contact in the Stage F ticket before staging artifacts on hardware.

## Sandbox-to-hardware replay sequence

1. **Stage sandbox artifacts.** Package the Stage C readiness bundle, Stage B
   rotation ledger, Stage E transport summaries, and the MCP handshake payloads
   into the Stage F submission so reviewers can confirm parity inputs before
   hardware replay.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_b_rotation_drills.jsonl†L12-L115】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】【F:logs/stage_c/20251001T010101Z-readiness_packet/mcp_drill/index.json†L1-L11】
2. **Validate tooling parity.** Confirm required toolchains, connectors, and
   telemetry exporters on the gate-runner host using the blueprint checklist
   before invoking the replay hook; log any deltas as
   `environment-limited: <reason>` in the Stage F packet and roadmap callouts.【F:docs/system_blueprint.md†L612-L667】【F:docs/documentation_protocol.md†L45-L70】
3. **Execute automation hook.** Run the Stage F automation on the reserved
   hardware window to stream parity traces, rollback drills, and telemetry
   snapshots into the Stage F evidence bundle while mirroring sandbox tagging
   for any deferred dependencies.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】
4. **Capture evidence snapshots.** Export Grafana dashboards, MCP heartbeat
   diffs, and Neo-APSU servant telemetry from the hardware run and attach them
   alongside the sandbox bundle to keep the lineage verifiable.【F:docs/system_blueprint.md†L612-L667】【F:logs/stage_c/20251001T010101Z-readiness_packet/checklist_logs/README.md†L1-L16】
5. **Record approvals.** File sign-offs from the operator lead, hardware owner,
   and QA reviewer using the same checklist cadence established during the
   Stage G bridge so parity lineage remains traceable through GA.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml†L1-L12】

## Role sign-off checklists

Each role completes the checklist below, attaches the required snapshots to the
Stage F evidence bundle, and signs the acknowledgement line.

### Operator lead checklist

| Item | Required evidence snapshot | Status |
| --- | --- | --- |
| ✅ Sandbox bundle staged with Stage B/Stage C/Stage E artifacts | `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json`, `logs/stage_b_rotation_drills.jsonl`, `logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json` | [ ] Complete |
| ✅ Gate-runner automation hook dry-run executed | Stage F evidence bundle `operator_hook.md` with console capture, linked to Stage C readiness checklist summary | [ ] Complete |
| ✅ Grafana dashboard export queued for hardware replay | Stage F evidence bundle `grafana_snapshot.png` covering panels defined in Stage C readiness checklist | [ ] Complete |

- **Operator lead signature:** ____________________ **Date:** __________

### QA reviewer checklist

| Item | Required evidence snapshot | Status |
| --- | --- | --- |
| ✅ Hash comparison between sandbox and hardware bundles archived | Stage F evidence bundle `hash_report.json`, sandbox baseline manifests | [ ] Complete |
| ✅ MCP heartbeat replay verified | `logs/stage_c/20251001T010101Z-readiness_packet/mcp_drill/index.json` baselines + hardware capture `mcp_heartbeat.json` | [ ] Complete |
| ✅ Environment-limited skips mirrored in roadmap and ticket notes | Roadmap Stage F callout diff, `docs/documentation_protocol.md` citation excerpt | [ ] Complete |

- **QA reviewer signature:** ____________________ **Date:** __________

### Neo-APSU owner checklist

| Item | Required evidence snapshot | Status |
| --- | --- | --- |
| ✅ Neo-APSU servant telemetry replayed with matching hashes | Stage F telemetry export `neoapsu_servant_hardware.csv`, sandbox baseline `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` sections | [ ] Complete |
| ✅ Route inevitability traces aligned with sandbox transcripts | Hardware `route_inevitability.log`, sandbox `logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json` sections | [ ] Complete |
| ✅ Approvals bundle signed and archived | Stage F approvals packet `approvals.yaml`, Stage G bridge approvals reference | [ ] Complete |

- **Neo-APSU owner signature:** ____________________ **Date:** __________

Stage F promotion is blocked until the hardware replay reproduces the sandbox
hashes for every Neo-APSU module above and captures the signed approvals bundle
referencing the scheduled hardware window.
