# Code Style Guide

This project follows a lightweight style that is largely compatible with
[PEP&nbsp;8](https://peps.python.org/pep-0008/) and the conventions used in the
existing code base. The following guidelines should be observed when submitting
changes.

## General
- Target **Python 3.10** or later.
- Use **4 spaces** per indentation level. Tabs are not allowed.
- Keep lines under **88 characters** when practical.
- Use `from __future__ import annotations` at the top of new modules that make
  use of forward references.
- Organise imports in three groups separated by blank lines: standard library,
  third‑party packages, and local modules.
- Prefer `pathlib.Path` over raw string paths.

## Naming
- Modules and packages use **lower_case_with_underscores**.
- Classes use **CapWords**.
- Functions and variables use **lower_case_with_underscores**.
- Constants are written in **UPPER_CASE_WITH_UNDERSCORES**.

## Docstrings and Comments
- Public modules, classes and functions should include **triple‑quoted
  docstrings** describing purpose and parameters.
- Use one line of summary followed by a blank line and additional details.
- Inline comments should be short and start with a capital letter.

## Typing
- Type hints are encouraged and should cover public function signatures.
- When returning multiple values, prefer named tuples or dataclasses.

## Tests
- Test files live under the `tests/` directory and use `pytest`.
- Tests should mock external network calls and avoid reliance on remote
  services.
- Keep test function names descriptive using `snake_case`.

## Commit Messages
- Write short, present‑tense commit titles (e.g. "Add GLM endpoint setting").
- Include a brief body if the change is not self‑explanatory.

Following this guide helps keep the code base consistent and easy to read for
new contributors.
