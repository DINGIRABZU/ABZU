# Contributing

Thank you for your interest in improving ABZU! This guide covers environment
setup, coding conventions, testing, and the pull request process. For a hands-on
orientation to the codebase—including environment setup, chakra overview,
architecture diagrams, a CLI quick-start, and troubleshooting tips—see the
[developer onboarding guide](docs/developer_onboarding.md).

For the project's overarching direction and boundaries, review
[docs/VISION.md](docs/VISION.md) and [docs/MISSION.md](docs/MISSION.md).

For details on chakra module architecture, version history, and contemplative
context, consult
[docs/chakra_architecture.md](docs/chakra_architecture.md),
[docs/chakra_versions.json](docs/chakra_versions.json), and
[docs/chakra_koan_system.md](docs/chakra_koan_system.md) – keep verses aligned
with version bumps.
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

## Pull Requests

- Keep changes focused; submit separate PRs for unrelated fixes.
- Ensure documentation is updated and tests pass.
- Lint Markdown files with `markdownlint` and verify links using `markdown-link-check`.
- Request review from a maintainer and address feedback promptly.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
