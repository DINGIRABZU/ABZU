# Razor Migration Playbook

## Python→Rust Parity Checklist
- Audit existing Python features and map each to the `neoabzu_razor` crate.
- Align public APIs and configuration files.
- Document APSU sequence placement referencing [blueprint_spine.md](../blueprint_spine.md) and [system_blueprint.md](../system_blueprint.md).

## Test Expectations
- Execute unit and integration tests for both Python and Rust paths.
- Confirm cross-language regression tests pass before merging.
- CI must report green across all gates.

## Rollback Steps
- Retain the last stable Python release behind a feature flag.
- If Rust defects surface, revert to the Python module and redeploy.
- Record rollback rationale in the component changelog.

