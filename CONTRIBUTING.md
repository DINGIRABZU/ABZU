# Contributing

To run the test suite you need a few Python packages:

- `numpy`
- `scipy`
- `soundfile`
- `librosa`
- `pytest`

Install them with:

```bash
pip install -r dev-requirements.txt
```

You can also run the helper script which prints a brief warning about the
download size:

```bash
./scripts/install_test_deps.sh
```

## Dependency lock file

Runtime dependencies are pinned in `requirements.lock` which is generated from
`pyproject.toml`.

After modifying dependencies, refresh the lock file and commit the result:

```bash
uv pip compile --no-deps pyproject.toml -o requirements.lock
```

# Coding Style

Follow the conventions in [CODE_STYLE.md](CODE_STYLE.md):

- Target Python 3.10+, use four spaces for indentation, and keep lines under 88 characters.
- Organise imports into standard library, third‑party, and local groups separated by blank lines.
- Include docstrings for public modules, classes, and functions.

# Static Typing

Static type checks run via `mypy` using defaults defined in `mypy.ini` such as
`ignore_missing_imports = true` and `disallow_untyped_defs = true`. Run the
checker before committing:

```bash
mypy
```

Modules that require dynamic behaviour are relaxed through per‑module overrides
inside `mypy.ini` (e.g. `INANNA_AI_AGENT.inanna_ai`, `INANNA_AI_AGENT.preprocess`).

# Testing Expectations

Run the test suite and basic smoke tests before opening a pull request:

```bash
scripts/smoke_console_interface.sh
scripts/smoke_avatar_console.sh
pytest --maxfail=1 -q
```

Code coverage is enforced at 85%. Generate a report locally to ensure the
threshold is met:

```bash
coverage run -m pytest
coverage report
```

# Pull Request Guidelines

- Keep changes focused; submit separate PRs for unrelated fixes.
- Ensure tests pass and documentation is updated.
- Request review from a maintainer and address feedback promptly.

