# Changelog for `rag.orchestrator`

All notable changes to this component will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### API Changes
- Added `VersionInfo` dataclass and `__version__` constant for explicit semantic versioning.
- `retrieve_top` now orchestrates hybrid retrieval across memory and external
  connectors, marking the component feature-complete in Rust.
- `merge_documents`, `retrieve_top`, and `MoGEOrchestrator.route` accept
  connector plugins with custom ranking strategies.

### Bug Fixes
- Added logging and fallback behaviour when the invocation engine is unavailable or fails.

### Score
- No score changes.
