# Contributor Checklist

This checklist distills mandatory practices for ABZU contributors.

## Triple-Reading Rule
- Read [blueprint_spine.md](blueprint_spine.md) **three times** before making changes. The repetition ensures deep architectural awareness as required by [The Absolute Protocol](The_Absolute_Protocol.md).

## Documentation Doctrine
- Run `python scripts/audit_doctrine.py` to confirm key docs exist, required index entries are present, and doctrine rules remain intact. The pre-commit hook executes this automatically when documentation changes.
- Review [chakra_metrics.md](chakra_metrics.md) to ensure monitoring aligns with chakra standards.
- Document connector protocol and heartbeat metadata in relevant guides. Every connector change must update these docs and pass `python scripts/check_connectors.py`.

## Self-Healing Commitment
- Affirm reading [self_healing_manifesto.md](self_healing_manifesto.md) before contributing.

## Error Index Updates
- Record recurring issues in [error_registry.md](error_registry.md).
- Update entries whenever new error patterns are resolved or observed.

## Test Requirements
- Run `pre-commit run --files <changed files>` on every commit.
- Run `python scripts/check_connectors.py` and fix any flagged connectors.
- Execute relevant tests with `pytest`. Document failing tests in [testing/failure_inventory.md](testing/failure_inventory.md) before merging.

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-10-25 | Initial checklist. |
| 0.1.1 | 2025-09-04 | Replace verify_doctrine with audit_doctrine. |
| 0.1.2 | 2025-09-04 | Require chakra metrics review. |
| 0.1.3 | 2025-09-05 | Require self-healing manifesto affirmation. |
| 0.1.4 | 2025-09-06 | Replace check_mcp_connectors with check_connectors; require connector protocol and heartbeat docs. |
