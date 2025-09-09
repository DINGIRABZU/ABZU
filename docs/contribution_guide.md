# Contribution Guide

Thank you for considering a contribution!

## Development Workflow

1. Fork the repository and create a new branch.
2. Make your changes with clear, descriptive commits.
3. Ensure tests and linters pass locally.
4. Open a pull request with a summary of your changes.

## Component Registry

Add new modules to [component_priorities.yaml](component_priorities.yaml) with a priority (P1–P5), criticality tag (core or optional), and relevant issue categories (config, runtime, integration). RAZAR uses this registry to schedule startup and classify errors.

## Code Quality

- Follow the project's [coding style](coding_style.md).
- Include tests for new functionality.
- Run `pre-commit` on modified files.
- Run targeted security scans with `pre-commit run bandit --files <paths>`.

## Communication

- Use issues to propose significant changes before implementation.
- Be respectful and collaborative in discussions.
