# Crown Migration Playbook

## Python→Rust Parity Checklist
- Map Crown's Python orchestration flows to the `neoabzu_crown` crate.
- Sync command interfaces and configuration schemas.
- Verify APSU sequence alignment through [blueprint_spine.md](../blueprint_spine.md) and [system_blueprint.md](../system_blueprint.md).

## Test Expectations
- Run existing Crown Python tests alongside Rust integration tests.
- Validate end-to-end mission routing under both implementations.
- Merge only after CI and mission demos succeed.

## Rollback Steps
- Keep the Python Crown router available as an emergency path.
- Re-enable Python and redeploy if Rust routing fails.
- Log rollback actions and update the release notes.

