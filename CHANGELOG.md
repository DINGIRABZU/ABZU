# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation Audit

- Ensure components have descriptions and data-flow references.
- Linked chakra koan and version files from README and CONTRIBUTING.
- Added chakra status table in `docs/chakra_status.md` outlining capabilities,
  limitations and planned evolutions for each layer.
- Linked release notes to `docs/chakra_versions.json` and `CHANGELOG.md`.
- Added recovery playbook documenting snapshot restoration steps.
- Mapped cortex, emotional, mental, spiritual and narrative memory stores in
  `docs/memory_architecture.md`.
- Introduced co-creation and AI ethics frameworks with cross-links from README and The Absolute Protocol.
- Added hyperlink requirement and illustrative component table to The Absolute Protocol.
- Required configuration files to include schema outlines and minimal examples, referencing `boot_config.json`, `razar_env.yaml`, and log formats.

### Quality

- Verified repository passes `ruff` and `black` checks.

### Vector Memory

- `snapshot` logs paths to `snapshots/manifest.json` for recovery tracking.
- Comments mention narrative hooks for cross-story references.

### Narrative Engine

- Stubbed `memory/narrative_engine.py` defining story event interfaces.

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
