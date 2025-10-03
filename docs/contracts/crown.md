# Crown Module Contract

## Overview
The crown contract documents orchestration between the decider, servant registry, and prompt orchestrator when bootstrapping a mission. It captures how servant endpoints are registered from configuration, how decision history drives LLM selection, and what telemetry reviewers should expect during sandbox boot.

## Sample Inputs and Outputs
- **Servant bootstrap.** Initialization reads a YAML configuration (empty in tests) and discovers servant endpoints via environment variables such as `DEEPSEEK_URL`, `MISTRAL_URL`, and `KIMI_K2_URL`, registering each under the servant model manager.【F:tests/crown/test_servant_registration.py†L27-L56】
- **Dynamic registry override.** Setting `SERVANT_MODELS="alpha=http://a,beta=http://b"` yields a registry containing both aliases after initialization, demonstrating the parsing contract for comma-separated `name=url` pairs.【F:tests/crown/test_servant_registration.py†L59-L85】
- **Decision scoring.** The decider inspects emotional memory history records and affect scores; when the latest successful entries for model "B" report higher joy/trust, `recommend_llm("instructional", "joy")` returns "B".【F:tests/crown/test_decider.py†L26-L74】

## Expected Logging and Telemetry
- Malformed servant entries trigger warnings such as "Skipping malformed SERVANT_MODELS entry" and "Duplicate servant model name" while still registering valid endpoints, ensuring operators see hygiene issues without breaking boot.【F:tests/crown/test_servant_registration.py†L88-L120】
- Sandbox runtime hooks automatically stub heavy dependencies (`crown_decider`, `crown_prompt_orchestrator`, `servant_model_manager`) so tests emit `EnvironmentLimitedWarning` rather than import failures when native crates are missing.【F:scripts/_stage_runtime.py†L27-L63】

## Failure Modes and Recovery
- **Configuration errors.** A malformed `SERVANT_MODELS` token (missing `=`) causes initialization to log warnings and skip the invalid entry; duplicates collapse to the first occurrence, preserving deterministic routing.【F:tests/crown/test_servant_registration.py†L88-L120】
- **Registry validation.** If every entry is malformed (for example `SERVANT_MODELS="brokenpair"`), the process exits, prompting operators to fix configuration before running production handoffs.【F:tests/crown/test_servant_registration.py†L123-L148】
- **Dependency shims.** Audio-analysis libraries (`librosa`, `opensmile`, `soundfile`) and NumPy functions are stubbed for the decider tests, illustrating the minimum interface required for sandbox-compatible emotional scoring.【F:tests/crown/test_decider.py†L12-L73】

## Reusable Fixtures and Stubs
- Reuse the servant-registration monkeypatches from `tests/crown/test_servant_registration.py` when crafting contract tests that simulate HTTP pings and registry hydration.【F:tests/crown/test_servant_registration.py†L27-L120】
- The decider history objects created in `tests/crown/test_decider.py` serve as canonical emotional-memory records for verifying scoring heuristics in future suites.【F:tests/crown/test_decider.py†L33-L74】
- Leverage `_stage_runtime`'s sandbox override registry to preload servant and decider modules before test execution, ensuring parity with the automation harness.【F:scripts/_stage_runtime.py†L27-L108】

## Future Work
Neo‑APSU adoption requires replaying Stage B rotation windows and Stage C readiness hashes on hardware before graduating the Rust `neoabzu_crown` decision path; the roadmap outlines how Stage D–H bundles carry those parity diffs and approvals.【F:docs/roadmap.md†L187-L193】 Contract dashboards must surface REST↔gRPC transport parity alongside crown telemetry so reviewers can trace sandbox warnings and servant registry status into Stage E beta gates and Stage G hardware replays.【F:docs/roadmap.md†L170-L218】 Continue flagging sandbox overrides with `EnvironmentLimitedWarning` until the hardware bridge enables native audio and emotional pipelines.【F:scripts/_stage_runtime.py†L27-L63】
