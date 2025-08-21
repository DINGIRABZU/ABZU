# Project Status

This document summarizes the current state of the ABZU codebase. It serves as a living roadmap covering repository layout, milestones, open issues, and release targets.

## Repository Structure

- **INANNA_AI/** – Core modules including adaptive learning, ethical validation, and audio analysis.
- **INANNA_AI_AGENT/** – Command line interface that activates the system and interacts with models.
- **audio/** – Audio processing utilities and backends for handling waveforms and feature extraction.
- **crown_config/** – Pydantic settings models and environment variable parsing.
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
  - Runtime warning: `pydub` could not find `ffmpeg` or `avconv` binaries.
  - PyTorch warning about nested tensor configuration.

These indicate gaps in the optional dependency stubs and missing system binaries.

## Milestones
- **Spiral OS stability** – integrate health checks and automated restart logic.
- **Pydantic v2 migration** – update all settings models to the new alias system.
- **Audio pipeline refresh** – add lazy loading and improve `pydub` fallbacks.

## Open Issues
- Optional dependencies (`numpy`, `stable_baselines3`, `gymnasium`) need robust stubs or lazy loading so minimal environments can import modules without errors.
- Pydantic models still use deprecated `Field` extras and require migration to aliases.
- FastAPI `@app.on_event` hooks should move to the `lifespan` API.
- Audio features depend on `pydub` and `ffmpeg`; availability checks and a NumPy fallback are recommended.

## Release Targets
- **v0.1** – minimal Spiral OS boot sequence and CLI tools (target: Q3 2025).
- **v0.2** – avatar console integration and basic RAG pipeline (target: Q4 2025).

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

