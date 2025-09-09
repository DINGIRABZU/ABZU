# CI Overview

This guide summarizes the repository's continuous integration workflow.

## Workflow jobs

- **change-justification** – verifies commits include a change justification.
- **pre-commit** – runs linting, formatting, and key-document checks.
- **bandit** – runs `pre-commit run bandit --all-files` to scan for high-severity,
  high-confidence issues. Address findings by fixing the code or adding an inline
  `# nosec` comment with a justification.
- **pytest** – executes the test suite with coverage, scans for TODO/FIXME markers, builds the component index, archives it under `data/archives/`, and verifies no stray files remain.
- **ci** – ensures documentation and configuration consistency and runs `mypy memory/ tests/` for type checking. The configuration ignores missing third-party stubs to provide a baseline signal.
- **server-smoke** – launches a minimal server test and validates API schemas.

The `pytest` job enforces ≥90% coverage and fails if placeholders or missing component statuses are detected.
