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
- Added module coverage and example run sections to the RAZAR agent guide.

### Changed
- Boot orchestrator now persists the handshake response before starting
  components and triggers `crown_model_launcher.sh` when `GLM4V` is absent.

## [0.1.0] - 2025-08-30

### Added
- Initial release of RAZAR runtime orchestrator and environment builder.

