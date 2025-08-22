# Coding Style

This document outlines the project's coding conventions.

## Type Hints

- Use Python type hints for all functions and methods, including return types.
- Prefer `typing` and `typing_extensions` for advanced types.

## Asynchronous Code

- Favor `async`/`await` for I/O-bound or concurrent tasks.
- Ensure coroutines are awaited and avoid blocking calls inside async functions.

## Testing Requirements

- Write unit tests with `pytest` for new features and bug fixes.
- Keep tests deterministic and isolated from external services.
- Run `pre-commit run --files <modified files>` before submitting changes.
