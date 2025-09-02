# CI Overview

This guide summarizes the repository's continuous integration workflow.

## Workflow jobs

- **change-justification** – verifies commits include a change justification.
- **pre-commit** – runs linting, formatting, and key-document checks.
- **bandit** – performs a security scan of the codebase.
- **pytest** – executes the test suite with coverage, scans for TODO/FIXME markers, builds the component index, archives it under `data/archives/`, and verifies no stray files remain.
- **ci** – ensures documentation and configuration consistency.
- **server-smoke** – launches a minimal server test and validates API schemas.

The `pytest` job enforces ≥90% coverage and fails if placeholders or missing component statuses are detected.
