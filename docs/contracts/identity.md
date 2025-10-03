# Identity Module Contract

## Overview
Identity synthesis blends mission, persona, and doctrine excerpts into a persisted summary that Crown broadcasts to downstream services. The contract describes how the loader interacts with the GLM integration, how embeddings are seeded into vector and corpus stores, and what telemetry confirms the identity fingerprint is ready.

## Sample Inputs and Outputs
- **Mission/persona merge.** `load_identity` concatenates mission and persona documents plus doctrine snippets before prompting the GLM; the resulting summary is written to `identity.json` and reused on subsequent calls without re-prompting.【F:tests/test_identity_loader.py†L24-L95】
- **Embedding side effects.** After initialization, the identity summary is pushed into both vector memory (`add_vector`) and corpus memory (`add_entry`) with metadata marking `type="identity_summary"` and `stage="crown_boot"`.【F:tests/test_identity_loader.py†L143-L176】
- **Handshake acknowledgement.** The GLM must respond with `CROWN-IDENTITY-ACK` when the loader sends the acknowledgement prompt; otherwise the loader raises an error and leaves no persisted summary, enforcing the handshake contract.【F:tests/test_identity_loader.py†L96-L121】

## Expected Logging and Telemetry
- Crown boot emits the `crown_identity_ready` gauge once the stored summary hash matches the generated fingerprint, as recorded in the system blueprint milestones.【F:docs/system_blueprint.md†L29-L37】
- Sandbox automation keeps `neoapsu_identity` in the forced-module override list so `_stage_runtime` can emit `EnvironmentLimitedWarning` when native bindings are missing instead of failing import, keeping telemetry intact for contract tests.【F:scripts/_stage_runtime.py†L27-L63】

## Failure Modes and Recovery
- **Ack mismatch.** If the GLM returns any string other than `CROWN-IDENTITY-ACK`, the loader aborts with a `RuntimeError`, prompting operators to troubleshoot mission/persona prompts or GLM connectivity before rerunning boot.【F:tests/test_identity_loader.py†L96-L121】
- **Missing doctrine artifacts.** Tests stub doctrine paths explicitly; real deployments should reuse the same path list to surface missing files early. Reapply the fixtures shown above when adding assertions about fingerprint deltas.【F:tests/test_identity_loader.py†L24-L95】
- **Vector ingestion gaps.** Should vector/corpus stores reject the identity entry, downstream retrieval lacks persona context. Use the `SimpleNamespace` stubs from the tests to verify metadata propagation while the sandbox vector memory remains stubbed.【F:tests/test_identity_loader.py†L143-L176】

## Reusable Fixtures and Stubs
- `DummyGLM` in the tests captures prompt history and emulates acknowledgement flow; reimport it for regression suites that exercise multi-step prompts.【F:tests/test_identity_loader.py†L12-L95】
- Monkeypatched vector/corpus memory stubs demonstrate the minimal interfaces (`add_vector`, `add_entry`) required for contract validation without the full Neo‑ABZU stack.【F:tests/test_identity_loader.py†L143-L176】
- `_stage_runtime` ensures `neoapsu_identity` stays patched during sandbox runs; call `bootstrap()` from that module when reproducing CLI behaviour so the same overrides apply.【F:scripts/_stage_runtime.py†L27-L108】

## Future Work
Identity readiness must promote the Rust loader and handshake pipeline onto gate-runner hardware, replaying Stage C readiness bundles and attaching Stage G parity approvals before removing sandbox overrides. The system blueprint already notes that each boot should publish a `CROWN_IDENTITY_FINGERPRINT`; extend that telemetry into Grafana once native bindings are enabled so reviewers can trace identity drift across hardware promotions.【F:docs/system_blueprint.md†L29-L37】 Document environment-limited skips emitted by `_stage_runtime` until the Neo‑APSU identity crate links successfully in CI and hardware runners, mirroring roadmap and PROJECT_STATUS updates for hardware bridge scheduling.【F:scripts/_stage_runtime.py†L27-L63】
