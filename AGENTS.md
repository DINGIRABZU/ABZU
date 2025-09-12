# AGENTS

- Always read [docs/documentation_protocol.md](docs/documentation_protocol.md) before editing documentation.
- Complete the onboarding checklist in [docs/onboarding/README.md](docs/onboarding/README.md) and confirm each item before starting code changes.
- Follow the naming and structuring conventions described there when creating new docs.
- Review and refresh [docs/system_blueprint.md](docs/system_blueprint.md) before committing changes to components or documentation.
- Consult [docs/The_Absolute_Protocol.md](docs/The_Absolute_Protocol.md) for core contribution rules.
- For Neo-APSU contributions, review [NEOABZU/docs/onboarding.md](NEOABZU/docs/onboarding.md) before touching code.
- Canonical doctrine is catalogued in [docs/doctrine_index.md](docs/doctrine_index.md); update it when altering foundational texts.
- Run `pre-commit run --files <modified files>` on all changed files before committing.
- Run `pre-commit run verify-onboarding-refs` to confirm `onboarding_confirm.yml` references core docs.
- Preserve the files listed in [docs/KEY_DOCUMENTS.md](docs/KEY_DOCUMENTS.md); a pre-commit hook fails if any are missing.

Deeper `AGENTS.md` files in subdirectories may override or extend these rules for files within their scope.
