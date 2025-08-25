# Changelog for `vector_memory`

All notable changes to this component will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### API Changes
- Added `VersionInfo` dataclass and `__version__` constant for explicit semantic versioning.
- Introduced automatic snapshots, on-disk compaction and `cluster_vectors` helper.
- Added `persist_snapshot` and `restore_latest_snapshot` helpers for manual snapshot persistence.

### Bug Fixes
- None.

### Score
- No score changes.
