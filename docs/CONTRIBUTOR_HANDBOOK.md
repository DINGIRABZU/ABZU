# Contributor Handbook

This handbook helps new contributors get set up, understand the repository layout, and work through common development workflows.

## Environment Setup

Install the required tools before working on the project:

- **Python 3.10+** – core runtime. Use a virtual environment.
- **pip** – install dependencies with `pip install -r requirements.txt`.
- **pre-commit** – run linters and formatters via `pre-commit install`.
- **Docker** *(optional)* – build and run containerized services.

Follow the [Code Style Guide](../CODE_STYLE.md) for formatting,
naming, and docstring conventions.

Key commands:

```bash
# install development dependencies
pip install -r dev-requirements.txt

# initialize pre-commit hooks
pre-commit install
```

For a full onboarding walkthrough, see the [Onboarding Walkthrough](onboarding_walkthrough.md) text guide. Additional reference documents are listed in the [Blueprint Export](BLUEPRINT_EXPORT.md).

## Repository Structure

| Path | Description |
|------|-------------|
| `docs/` | Project documentation and design notes. |
| `src/` | Core application packages. |
| `tests/` | Automated test suites. |
| `agents/` | Domain-specific agent implementations. |
| `tools/` | Utility scripts for maintenance and developer workflows. |

## Sample Workflows

### Running Tests

```bash
pytest
```

### Adding a Feature

1. Create or update tests in `tests/`.
2. Implement the feature in `src/` or relevant modules.
3. Update documentation in `docs/`.
4. If `src/` or top-level service files change, update `docs/system_blueprint.md`; a pre-commit hook enforces this.
5. Run `pre-commit run --files <changed_files>` and `pytest`.

### Submitting a Pull Request

1. Push your branch to GitHub.
2. Open a pull request and describe the changes.
3. Ensure CI checks pass and address review feedback.

## Further Reading

- [Onboarding Walkthrough](onboarding_walkthrough.md)
- [Onboarding Guide](onboarding_guide.md)
- [Blueprint Export](BLUEPRINT_EXPORT.md)
- [Contribution Guide](contribution_guide.md)
