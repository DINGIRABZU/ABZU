# Development Checklists

Quick links: [Developer Onboarding](developer_onboarding.md) | [Developer Etiquette](developer_etiquette.md)

## Mandatory Steps for Any Code Change
- Update related documentation and examples. The CI workflow fails if Python modules are changed without matching updates in `docs/`.
- Run `ruff` for linting.
- Run `black` for formatting.
- Run `mypy` for static type checks.
- Run tests with `pytest`.

## Adding a New Module
- Create the module with clear names and docstrings.
- Add tests covering the new functionality.
- Register the module in any relevant index or package `__init__`.
- Update documentation and the change log.
- Complete the mandatory steps above.

## Changing APIs
- Update function and class docstrings and user guides.
- Adjust dependent modules and examples.
- Add or update tests that exercise the new API.
- Note the change in the change log and API references.
- Complete the mandatory steps above.

## Modifying Data Schemas
- Revise schema definitions and example payloads.
- Document migration or compatibility notes.
- Update tests and fixtures for the new schema.
- Bump schema versions and update consumers.
- Complete the mandatory steps above.
