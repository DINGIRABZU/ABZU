# Key Documents

The files listed here are foundational and must never be deleted or renamed.

## Protected Files

- [AGENTS.md](../AGENTS.md)
- [The Absolute Protocol](The_Absolute_Protocol.md)

These documents define repository-wide conventions and rules. Repository policy and pre-commit checks prevent their removal or renaming.

Contributors must also record a brief summary of each protected document in `onboarding_confirm.yml`. Each summary should describe the document's **purpose**, **scope**, and **key rules**.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create an `onboarding_confirm.yml` file in the repository root that records the hash and summary of each required document:

```yaml
documents:
  AGENTS.md:
    sha256: <sha256>
    summary: "Guidelines for repository operations and agent conduct."
  docs/The_Absolute_Protocol.md:
    sha256: <sha256>
    summary: "Core contribution rules and governance."
```

The `confirm-reading` pre-commit hook verifies this file and blocks commits if any listed document changes.
