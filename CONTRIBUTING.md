# Contributing

Thank you for your interest in improving ABZU! This guide covers environment
setup, coding conventions, testing, and the pull request process. For a hands-on
orientation to the codebase—including environment setup, chakra overview,
architecture diagrams, a CLI quick-start, and troubleshooting tips—see the
[developer onboarding guide](docs/developer_onboarding.md).

Before committing changes, review the
[development checklists](docs/development_checklist.md) for mandatory steps and
guidance on adding modules, updating APIs, or altering data schemas.

For the project's overarching direction and boundaries, review
[docs/VISION.md](docs/VISION.md) and [docs/MISSION.md](docs/MISSION.md).

For details on chakra module architecture, version history, and contemplative
context, consult
[docs/chakra_architecture.md](docs/chakra_architecture.md) and the paired
manifest in [docs/chakra_versions.json](docs/chakra_versions.json) with its
verses in [docs/chakra_koan_system.md](docs/chakra_koan_system.md) – keep them
aligned with version bumps.
For a request pipeline diagram and chakra quality table, see [docs/data_flow.md](docs/data_flow.md) and [docs/chakra_overview.md](docs/chakra_overview.md).

Operational fallbacks and recovery steps are outlined in
[docs/essential_services.md](docs/essential_services.md).

When bumping versions in
[docs/chakra_versions.json](docs/chakra_versions.json), record the change in
[CHANGELOG.md](CHANGELOG.md).

## Setup

Use Python 3.10 or later. Install development dependencies with:

```bash
pip install -r dev-requirements.txt
```

A helper script prints a brief warning about download size:

```bash
./scripts/install_test_deps.sh
```

Runtime dependencies are pinned in `requirements.lock` which is generated from
`pyproject.toml`. After modifying dependencies, refresh the lock file and commit
the result:

```bash
uv pip compile --no-deps pyproject.toml -o requirements.lock
```

### Pre-commit Hooks

Linting tools are pinned in `.pre-commit-config.yaml` for reproducibility. When
dependencies change or on a regular cadence, refresh the hooks and commit the
result:

```bash
pre-commit autoupdate
pre-commit run --files .pre-commit-config.yaml
git add .pre-commit-config.yaml
```

Create a separate commit (e.g. `chore: update pre-commit hooks`) so the update
is easy to track.

## Coding Style

Follow the conventions in [CODE_STYLE.md](CODE_STYLE.md). Highlights include:

- Four spaces per indentation level and lines under 88 characters.
- Imports grouped into standard library, third‑party, and local sections.
- Docstrings for public modules, classes, and functions.

Run the standard tooling before committing changes:

```bash
ruff <paths>    # lint
black <paths>   # format
mypy            # type check
```

## Testing

Execute smoke tests, the health scanner, and the unit test suite before submitting changes:

```bash
scripts/smoke_console_interface.sh
scripts/smoke_avatar_console.sh
python scripts/vast_check.py http://localhost:8000
pre-commit run --all-files
pytest --maxfail=1 -q
```

Code coverage is enforced at 85%. Generate a report locally to ensure the
threshold is met:

```bash
coverage run -m pytest
coverage report
```

## Component Version Mandate

Every source module must define a `__version__` attribute. Bump this value for
any user-facing change and keep entries synchronized in
`component_index.json`. The `verify-versions` pre-commit hook scans staged
Python files and fails if the attribute is missing.

## Connector Guidelines

Connector modules bridge ABZU to external services. They must expose
`__version__` and update the canonical registry at
[`docs/connectors/CONNECTOR_INDEX.md`](docs/connectors/CONNECTOR_INDEX.md)
whenever a connector is added, removed, or modified.

## Contributor Awareness Checklist

Before submitting a pull request, confirm:

- **Key documents reviewed**
  - `AGENTS.md` – repository-wide agent instructions
  - `docs/documentation_protocol.md` – documentation workflow
  - `docs/system_blueprint.md` – architecture overview
  - `docs/KEY_DOCUMENTS.md` – critical files with review cadences
- **Version bumps**
  - Increment `__version__` in all affected modules and connectors
  - Update connector registry entries after interface changes
- **Change justification**
  - Summarize the purpose of modifications in commits and the PR description

## Pull Requests

- Prefix pull request titles with a category such as `Feature:`, `Fix:`, or `Chore:` (e.g., `Feature: Voice Cloning V2`).
- Keep changes focused; submit separate PRs for unrelated fixes.
- Ensure documentation is updated and tests pass.
- Pull requests that fail `pre-commit run --all-files` will not be merged.
- Register new modules in [docs/component_priorities.yaml](docs/component_priorities.yaml) with a priority (P1–P5), criticality tag, and issue categories so RAZAR can orchestrate startup.
- Record project-wide documentation or architectural changes in
  [docs/system_blueprint.md](docs/system_blueprint.md) by adding a new
  version entry; do not modify or remove prior content. After updates, run
  `python tools/doc_indexer.py` to refresh `docs/INDEX.md`.
- Lint Markdown files with `markdownlint` and verify links using `markdown-link-check`.

### Review Process

ABZU uses two reviewer tiers:

1. **Maintainer review (required):** Every PR must be reviewed by at least one project maintainer.
2. **Domain expert review (optional):** For changes touching specialized areas such as security, infrastructure, or ML pipelines, request a review from a domain expert. Mention the domain in the PR description and tag the appropriate expert or ask a maintainer to loop them in.

**Reviewer expectations:** Ensure tests and linters pass, confirm documentation and style guidelines are followed, and provide constructive feedback. Escalate to additional reviewers if deeper expertise is needed.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
