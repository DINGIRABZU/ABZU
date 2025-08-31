# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation Audit

- Mandated quarterly review of entries in `docs/KEY_DOCUMENTS.md` and added audit cadence table with `scripts/schedule_doc_audit.py`.
- Ensure components have descriptions and data-flow references.
- Linked chakra koan and version files from README and CONTRIBUTING.
- Added chakra status table in `docs/chakra_status.md` outlining capabilities,
  limitations and planned evolutions for each layer.
- Linked release notes to `docs/chakra_versions.json` and `CHANGELOG.md`.
- Added recovery playbook documenting snapshot restoration steps.
- Mapped cortex, emotional, mental, spiritual and narrative memory stores in
  `docs/memory_architecture.md`.
- Added INANNA core deployment notes and memory component entries in
  `component_index.json`.
- Documented RAZAR environment configuration schema in `docs/RAZAR_AGENT.md`.
- Added `__version__` fields across modules and added version checks in `scripts/component_inventory.py`.
- Documented Nazarick agent triggers for Albedo state transitions and added
  state-to-channel table; refreshed `docs/INDEX.md`.


### Documentation

- Updated Nazarick narrative system guide with mermaid pipeline diagram and removed obsolete image reference.
- Added Albedo layer state-machine diagram and deployment guide with sample configuration.
- Expanded Nazarick agent guide with deployment commands, channel mappings, and extensibility hooks.
- Documented Nazarick Web Console with mermaid layout diagram, dependencies, and connector links.
- Added "The Absolute pytest" guide for chakra-aligned tests and commit workflow.
- Introduced Pytest Protocol with >90% coverage, chakra-aligned directories, and component index documentation requirements.
- Expanded Crown agent overview with model loading sequence diagram and configuration table.
- Documented change justification rule and mandated four-part onboarding summaries; updated pull request template with connector/index checklist.
- Documented module coverage and example runs in RAZAR agent guide.
- RAZAR agent guide now requires `CROWN_WS_URL`, a running Crown server, and
  documents mission brief archive rotation.
- Added Change Justification subsection and PR template field with CI validation.
- Protocol v1.0.60 now requires `__version__` in every module, connector, and service and mandates documenting configuration schemas (e.g., `boot_config.json`, `primordials_config.yaml`, `operator_api.yaml`) with examples.
- Linked Operator Protocol from RAZAR agent guide and regenerated docs index.

### Added

- Introduced protocol compliance dashboard and required dashboard updates each release cycle in The Absolute Protocol.
- Introduced lifecycle `status` and `adr` link requirements for `component_index.json` and provided `docs/adr/ADR_TEMPLATE.md`.
- Introduced co-creation and AI ethics frameworks with cross-links from README and The Absolute Protocol.
- Expanded connector registry schema with purpose and service fields and updated The Absolute Protocol accordingly.
- Added Code Harmony, API Contract, and Technology Registry protocols to The Absolute Protocol.
- Created connector index and documented registry rules in The Absolute Protocol.
- Added hyperlink requirement and illustrative component table to The Absolute Protocol.
- Added checklist reminder to update `CONNECTOR_INDEX.md` whenever connectors change.
- Required configuration files to include schema outlines and minimal examples, referencing `boot_config.json`, `razar_env.yaml`, and log formats.
- Added operator protocol for `/operator/command` and linked it under Subsystem Protocols in The Absolute Protocol.
- Mandated end-to-end run examples with logs covering normal operation and failure recovery in agent docs.
- Archived Crown handshake responses alongside mission briefs and
  auto-launched `GLM4V` when missing from advertised capabilities.
- Persisted Crown handshake acknowledgement and downtime under `handshake`
  in `logs/razar_state.json`.
- Logged handshake and model-launch events in `logs/razar_state.json` and mandated mission-brief logging for all handshakes in The Absolute Protocol.
- Required a "Change justification" field in the pull request template and documented the statement format in The Absolute Protocol.
- Documented mission brief archive requirements and maintenance in The Absolute Protocol.
- Added Operator API and Open Web UI entries to `CONNECTOR_INDEX.md` and expanded protocol checklist for connector registry.
- Required onboarding summaries for all files listed in `onboarding_confirm.yml` and referenced the rule in The Absolute Protocol.
- Added Release Protocol to The Absolute Protocol covering changelog updates, git tagging, and release note cross-references.
- Clarified Release Management Protocol with semantic versioning rules and checklist references.
- Required logging of RAZAR ↔ Crown ↔ Operator exchanges in `logs/interaction_log.jsonl` and referenced rules in RAZAR and operator docs.
- Enforced Crown availability during boot and rotated mission brief archives under `logs/mission_briefs/`.
- Added Connector Guidelines section requiring version fields, endpoint documentation, and registry updates, enforced by a pre-commit check.
- Crown prompt orchestrator reviews test metrics and logs remediation suggestions to corpus memory.
- Extended Operator API and web console to support file uploads with metadata relayed to RAZAR via Crown, and documented `/operator/upload` authentication and rate limits.
- Added configurable audio and video track helpers with fallbacks to WebRTC server and connector.
- Pytest runs export coverage, session duration, and failure metrics via `prometheus_client` to `monitoring/pytest_metrics.prom`, and CI uploads the metrics artifact.
- Implemented AI handover workflow that delegates failures to remote agents,
  logging invocations and applied patch diffs.
- AI handover now reads configurable agent endpoints and authentication
  tokens and retries components after automated patches are applied.
- Routed INANNA interactions through Bana, storing narratives in spiral memory
  and relaying quality metrics to the Primordials service.

### Quality

- Verified repository passes `ruff` and `black` checks.
- Enforced "No Placeholder" rule with `check-placeholders` pre-commit hook and
  documented remediation steps in agent guides.

### Vector Memory

- `snapshot` logs paths to `snapshots/manifest.json` for recovery tracking.
- Comments mention narrative hooks for cross-story references.

### Narrative Engine

- Expanded anonymized biosignal datasets with acquisition guidelines and
  ingestion script references.
- Extended tests to cover multiple samples and transformations.
- Introduced `sample_biosignals_gamma.csv` and documented ingestion schema with
  dedicated transformation tests.
- Stubbed `memory/narrative_engine.py` defining story event interfaces.
- Added `docs/nazarick_narrative_system.md` outlining architecture, dependencies,
  and biosignal event flow.
- Added `sample_biosignals_delta.csv` with schema and ingestion notes.
- Enhanced tests to validate numeric data and multi-file transformations.

### Chakra Versions

- Track semantic versions for each chakra layer in
  `docs/chakra_versions.json`.
- Record each chakra version bump in this changelog.
- Bumped `root` and `crown` chakras to `1.0.1`.
- Bumped `sacral` chakra to `1.0.1`.
- Bumped `heart` chakra to `1.0.1`.
- Bumped `solar_plexus` chakra to `1.1.0` after learning pipeline updates; see `docs/chakra_koan_system.md#solar`.
- Bumped `throat` chakra to `1.0.1` fixing prompt orchestration; see `docs/chakra_koan_system.md#throat`.
- Synced heart koan reference with the manifest.
- Bumped `third_eye` chakra to `1.0.1` for narrative memory integration.

### Insight Matrix

- Record versioned history of insight matrix updates in `insight_manifest.json`.

## [0.1.0] - 2025-08-23

### Added

- Initial release.
