# Changelog for `razar`

All notable changes to this component will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documented remediation steps for placeholder violations in RAZAR agent
  guide.
- Added logging requirement for RAZAR ↔ Crown ↔ Operator exchanges in `logs/interaction_log.jsonl`.
- Persisted CROWN handshake responses to `logs/mission_briefs/` and
  triggered `crown_model_launcher.sh` when `GLM4V` capability is absent.
- Stored Crown handshake acknowledgement, capabilities, and downtime under
  `handshake` in `logs/razar_state.json`.
- Logged handshake and model-launch events in `logs/razar_state.json` and documented event persistence in the deployment guide.
- Archived GLM-4.1V launch events to `logs/mission_briefs/` and added tests
  for mission-brief archiving and GLM capability detection.
- Added module coverage and example run sections to the RAZAR agent guide.
- Rotated mission brief archives and required Crown availability via `CROWN_WS_URL` before boot.
- Delegated failure recovery to remote agents via `ai_invoker.handover` and
  logged invocations and patch results.
- Added retry logic and patch-attempt logging to `ai_invoker.handover`.
- Added `scripts/validate_ignition.py` to traverse the RAZAR → Crown → INANNA → Albedo → Nazarick → operator interface chain and capture readiness in `logs/ignition_validation.json`.
- Linked environment schema and example fields in the RAZAR agent guide.
- Recorded applied patch diffs in `logs/razar_ai_patches.json`.
- Linked Operator Protocol guide from the RAZAR agent cross-links section.
- Added configurable agent endpoints and authentication tokens to
  `ai_invoker.handover` and retried components after patches are applied.
- Operator uploads now store files under operator-specific paths and relay metadata through Crown to RAZAR.
- Expanded remote assistance workflow with sequence diagram and dedicated invocation and patch logs.
- Detailed handover and patch application flow with `ai_invoker` → `code_repair` diagram and patch log reference.
- Added unit tests for `ai_invoker.handover` and `code_repair.repair_module`.

- Expanded guide with architecture diagram, requirements, deployment workflow, config schemas, cross-links, and example runs.
### Changed
- Boot orchestrator now persists the handshake response before starting
  components and triggers `crown_model_launcher.sh` when `GLM4V` is absent.

## [0.1.0] - 2025-08-30

### Added
- Initial release of RAZAR runtime orchestrator and environment builder.

