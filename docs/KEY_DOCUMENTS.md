# Key Documents

The files listed here are foundational and must never be deleted or renamed.

## Protected Files

- [AGENTS.md](../AGENTS.md)
- [The Absolute Protocol](The_Absolute_Protocol.md)

These documents define repository-wide conventions and rules. Repository policy and pre-commit checks prevent their removal or renaming.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create a `.reading_complete` file in the repository root:

```bash
touch .reading_complete
```

A pre-commit hook blocks commits until this marker exists.
