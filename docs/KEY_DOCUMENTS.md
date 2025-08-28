# Key Documents

The files listed here are foundational and must never be deleted or renamed.

## Protected Files

- [AGENTS.md](../AGENTS.md)
- [The Absolute Protocol](The_Absolute_Protocol.md)

These documents define repository-wide conventions and rules. Repository policy and pre-commit checks prevent their removal or renaming.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create an `onboarding_confirm.yml` file in the repository root that records the hash of each required document:

```yaml
documents:
  docs/architecture_overview.md: <sha256>
  docs/The_Absolute_Protocol.md: <sha256>
```

The `confirm-reading` pre-commit hook verifies this file and blocks commits if any listed document changes.
