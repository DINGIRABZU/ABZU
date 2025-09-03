# Contributor Checklist

This checklist distills mandatory practices for ABZU contributors.

## Triple-Reading Rule
- Read [blueprint_spine.md](blueprint_spine.md) **three times** before making changes. The repetition ensures deep architectural awareness as required by [The Absolute Protocol](The_Absolute_Protocol.md).

## Error Index Updates
- Record recurring issues in [error_registry.md](error_registry.md).
- Update entries whenever new error patterns are resolved or observed.

## Test Requirements
- Run `pre-commit run --files <changed files>` on every commit.
- Execute relevant tests with `pytest`. Document failing tests in [testing/failure_inventory.md](testing/failure_inventory.md) before merging.

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-10-25 | Initial checklist. |
