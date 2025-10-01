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

## Prerequisites

- **Toolchains.** Gate-runner hosts must expose the Rust toolchain, Python
  bridge utilities, and build prerequisites enumerated in the Neo-APSU
  onboarding guide so hardware parity binaries match the sandbox builds.【F:NEOABZU/docs/onboarding.md†L1-L36】
- **Sandbox evidence bundles.** Stage F runs start from the merged Stage C
  readiness bundle, Stage B rotation ledger, and Stage E transport readiness
  snapshot so every hardware replay references canonical sandbox artifacts and
  credential windows.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_b_rotation_drills.jsonl†L12-L115】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】
- **Scheduled hardware windows.** Reserve gate-runner execution slots aligned
  to the Stage C exit checklist and readiness minutes so the sandbox-to-hardware
  bridge meets The Absolute Protocol handoff requirements.【F:logs/stage_c/20250930T210000Z-stage_c1_exit_checklist/summary.json†L1-L33】【F:docs/The_Absolute_Protocol.md†L54-L114】

## Sandbox-to-hardware transition

1. **Assemble sandbox evidence.** Package the latest Stage C readiness bundle,
   Stage B rotation ledger, and Stage E transport summaries into the Stage F
   submission so reviewers can confirm parity inputs before hardware replay.【F:logs/stage_c/20251001T010101Z-readiness_packet/readiness_bundle/readiness_bundle.json†L1-L210】【F:logs/stage_b_rotation_drills.jsonl†L12-L115】【F:logs/stage_e/20250930T121727Z-stage_e_transport_readiness/summary.json†L1-L142】
2. **Execute hardware replay.** Run the Stage F automation hook on the
   scheduled gate-runner window to stream parity traces, rollback drills, and
   telemetry snapshots into the Stage F evidence bundle while tagging sandbox
   limitations as `environment-limited` where dependencies remain deferred.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/summary.json†L1-L13】【F:docs/documentation_protocol.md†L21-L49】
3. **Record approvals.** File sign-offs from the operator lead, hardware owner,
   and QA reviewer using the same checklist cadence established during the
   Stage G bridge so parity lineage remains traceable through GA.【F:logs/stage_g/20251102T090000Z-stage_g_gate_runner_hardware/approvals.yaml†L1-L12】【F:logs/stage_g/20251102T094500Z-stage_g_neo_apsu_parity/approvals.yaml†L1-L12】

Stage F promotion is blocked until the hardware replay reproduces the sandbox
hashes for every Neo-APSU module above and captures the signed approvals bundle
referencing the scheduled hardware window.
