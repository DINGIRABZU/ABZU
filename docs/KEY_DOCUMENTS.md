# Key Documents

The files listed here are foundational and must never be deleted or renamed.

## Protected Files

- [AGENTS.md](../AGENTS.md)
- [The Absolute Protocol](The_Absolute_Protocol.md)
- [System Blueprint](system_blueprint.md)
- [Component Index](component_index.md)
- [Component Status](component_status.md)
- [Connector Index](connectors/CONNECTOR_INDEX.md) (see [Connector Overview](connectors/README.md) for patterns and maintenance rules)

These documents define repository-wide conventions and rules. Repository policy and pre-commit checks prevent their removal or renaming. When related components change, update the corresponding document in the same commit to keep information synchronized.

Contributors must also record a brief summary of each protected document in `onboarding_confirm.yml`. Each summary should describe the document's **purpose**, **scope**, **key rules**, and include one **actionable insight**.

## Onboarding Confirmation

After completing the [onboarding checklist](onboarding/README.md), create an `onboarding_confirm.yml` file in the repository root that records the hash and summary of each required document:

```yaml
documents:
  AGENTS.md:
    sha256: <sha256>
    summary: "Guidelines for repository operations and agent conduct."
    insight: "Always run pre-commit on changed files."
  docs/The_Absolute_Protocol.md:
    sha256: <sha256>
    summary: "Core contribution rules and governance."
    insight: "Review checklist before opening a pull request."
```

The `confirm-reading` pre-commit hook verifies this file and blocks commits if any listed document changes.
The companion `verify-doc-summaries` hook recomputes hashes for all entries and
fails if `onboarding_confirm.yml` is out of date, ensuring stored summaries stay
aligned with their documents.
