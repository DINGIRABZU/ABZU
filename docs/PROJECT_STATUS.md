# Project Status

This document summarizes the current state of the ABZU codebase. It is intended to help new contributors understand the repository layout, test coverage, and outstanding issues.

## Repository Structure

- **INANNA_AI/** – Core modules including adaptive learning, ethical validation, and audio analysis.
- **INANNA_AI_AGENT/** – Command line interface that activates the system and interacts with models.
- **audio/** – Audio processing utilities and backends for handling waveforms and feature extraction.
- **config/** – Pydantic settings models and environment variable parsing.
- **connectors/** – Integrations with external services and APIs.
- **tests/** – Unit tests for learning modules, connectors, and audio helpers.
- **docs/** – Architecture overviews, deployment guides, and design notes.

## Test Run (pytest --maxfail=1 -q)

```
pytest --maxfail=1 -q
```

The test suite currently fails early:

- `tests/test_adaptive_learning.py::test_validator_feedback_updates_threshold` raises `AttributeError: 'types.SimpleNamespace' object has no attribute 'permutation'`.
- Warnings include:
  - Deprecation warning: `audioop` is deprecated and slated for removal in Python 3.13.
  - Runtime warning: `pydub` could not find `ffmpeg` or `avconv` binaries.
  - PyTorch warning about nested tensor configuration.

These indicate gaps in the optional dependency stubs and missing system binaries.

## Outstanding Issues

- Optional dependencies (`numpy`, `stable_baselines3`, `gymnasium`) need robust stubs or lazy loading so minimal environments can import modules without errors.
- Pydantic models still use deprecated `Field` extras and require migration to aliases.
- FastAPI `@app.on_event` hooks should move to the `lifespan` API.
- Audio features depend on `pydub` and `ffmpeg`; availability checks and a NumPy fallback are recommended.
- Upcoming Python releases will remove `audioop`; the audio pipeline must migrate away from this module.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

