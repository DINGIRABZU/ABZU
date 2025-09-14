# Migration Protocol

Guidelines for coordinating Python→Rust migrations across the codebase.

## Branching
- Create feature branches using `migration/<module>` naming.
- Rebase frequently on `main` to minimize drift.
- Update [system_blueprint.md](system_blueprint.md) if architecture shifts.

## Reviews
- Require at least two maintainers to approve migrations.
- Reference relevant playbooks in review descriptions.
- Link to APSU sequence diagrams such as [blueprint_spine.md](blueprint_spine.md).

## Release Gating
- All migrations must pass unit, integration, and regression tests.
- Documentation updates and index regeneration are mandatory.
- Releases are gated on successful rollback validation and changelog entries.

