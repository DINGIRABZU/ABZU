# Failure Inventory

This document summarizes test failures from `pytest -vv` run on 2025-08-30.

## Missing environment or resource
See [Missing dependency checklist](../the_absolute_pytest.md#missing-dependency-checklist).
- [tests/agents/razar/test_crown_link.py](../../tests/agents/razar/test_crown_link.py): Module `websockets` not installed.
  - *Suggested fix*: add `websockets` to project dependencies.
- [tests/crown/test_initialization.py](../../tests/crown/test_initialization.py): Module `omegaconf` not installed.
  - *Suggested fix*: install `omegaconf` or guard import behind optional dependency.
- [tests/test_operator_api.py](../../tests/test_operator_api.py): FastAPI requires `python-multipart` for form data.
  - *Suggested fix*: add `python-multipart` package.
- [tests/test_emotion_classifier.py](../../tests/test_emotion_classifier.py): scikit-learn raises `AttributeError` referencing `RandomState`.
  - *Suggested fix*: pin compatible `scikit-learn`/`numpy` versions.

## Data mismatch or library issue
See [Library compatibility checks](../the_absolute_pytest.md#library-compatibility-checks).
- [tests/test_dashboard_app.py](../../tests/test_dashboard_app.py) and [tests/test_dashboard_qnl_mixer.py](../../tests/test_dashboard_qnl_mixer.py): Plotly theme configuration sets a string where a numeric array is expected, causing `AttributeError: 'str' object has no attribute 'dtype'`.
  - *Suggested fix*: adjust Plotly configuration to supply numeric color values.

## Code defects / test configuration
See [Fixture-writing guidelines](../the_absolute_pytest.md#fixture-writing-guidelines).
- [tests/test_quarantine_manager.py](../../tests/test_quarantine_manager.py) and [tests/test_vector_memory.py](../../tests/test_vector_memory.py): `import file mismatch` due to duplicate test module names under different paths.
  - *Suggested fix*: rename one of the duplicate test modules or adjust `PYTHONPATH` to avoid conflicts.
- [tests/test_voice_cloner_cli.py](../../tests/test_voice_cloner_cli.py): `ImportError` for `load_config` in `core`.
  - *Suggested fix*: implement or expose `load_config` in `core` module.

## Unimplemented features
- (None identified)

See [pytest log](pytest.log) for full output.
