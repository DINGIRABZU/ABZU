# Code Style Guide

This project follows a lightweight style that is largely compatible with
[PEP&nbsp;8](https://peps.python.org/pep-0008/) and the conventions used in the
existing code base. The following guidelines should be observed when submitting
changes.

## Formatting
- Format code with [`black`](https://black.readthedocs.io/). The
  `pre-commit` hooks run Black automatically on staged files.
- Target **Python 3.10** or later.
- Use **4 spaces** per indentation level. Tabs are not allowed.
- Keep lines under **88 characters** when practical. Black enforces this
  limit.
- Use `from __future__ import annotations` at the top of new modules that make
  use of forward references.
- Organise imports in three groups separated by blank lines: standard
  library, third-party packages, and local modules.
- Prefer `pathlib.Path` over raw string paths.
- Encode files as **UTF‑8** and end them with a single trailing newline.
- Prefer **single quotes** for short strings and **f‑strings** for
  interpolation.
- Include **trailing commas** in multi-line collections to minimise diffs.

## Naming
The following conventions are checked by `flake8` rules via
[`ruff`](https://docs.astral.sh/ruff/):

- Modules and packages use **lower_case_with_underscores**.
- Classes use **CapWords**.
- Functions and variables use **lower_case_with_underscores**.
- Constants are written in **UPPER_CASE_WITH_UNDERSCORES**.
- Private helpers start with a single leading underscore.
- Choose descriptive names; avoid abbreviations unless they are
  universally understood.
- Use **nouns** for classes and **verbs** for functions.

## Docstrings and Comments
- Public modules, classes and functions should include **triple-quoted
  docstrings** describing purpose and parameters. PEP 257 compliance is
  validated with `pydocstyle` checks (run through `ruff`).
- Start with a one-line summary in the imperative mood, followed by a blank
  line and additional context.
- Inline comments should be short and start with a capital letter.
- Use **triple double quotes** (`"""`) for docstrings and keep them
  [PEP 257](https://peps.python.org/pep-0257/) compliant.
- Document arguments and return values in the docstring even when type hints
  are present. For complex APIs, prefer
  [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
  sections like `Args` and `Returns`.
- Provide example snippets in docstrings when behaviour is non-obvious.

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
