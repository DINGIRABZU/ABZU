# Project Status

![Coverage](../coverage.svg)

See [component_maturity.md](component_maturity.md) for per-component maturity metrics.

This document summarizes the current state of the ABZU codebase. It serves as a living roadmap covering repository layout, milestones, open issues, and release targets.

## Repository Structure

- **INANNA_AI/** – Core modules including adaptive learning, ethical validation, and audio analysis.
- **INANNA_AI_AGENT/** – Command line interface that activates the system and interacts with models.
- **audio/** – Audio processing utilities and backends for handling waveforms and feature extraction.
- **crown_config/** – Pydantic settings models and environment variable parsing.
- **connectors/** – Integrations with external services and APIs (see [Connector Index](connectors/CONNECTOR_INDEX.md)).
- **tests/** – Unit tests for learning modules, connectors, and audio helpers.
- **docs/** – Architecture overviews, deployment guides, and design notes.

## Test Run (pytest --maxfail=1 --cov -q)

```
pytest --maxfail=1 --cov -q
```

The suite currently reports numerous skips but completes without failures while generating coverage data:

- `9 passed, 447 skipped, 3 warnings`.
- Warnings include:
  - `pydub` could not find `ffmpeg` or `avconv` binaries.
  - PyTorch warning about nested tensor configuration.

Coverage is **1%**; the badge above reflects the latest report.

These results indicate optional dependencies and system binaries are still missing but do not block the minimal test run.

## Recent Refactoring

- Standardized import order in `tools.session_logger`, `tools.sandbox_session`, and `tools.reflection_loop`.
- Added smoke tests covering reflection and session logging utilities.
- Reordered imports in `learning_mutator`, `state_transition_engine`, and `archetype_shift_engine` and added transformation smoke tests.

## Completed Milestones
- [Sovereign voice pipeline](https://github.com/DINGIRABZU/ABZU/pull/38) — owner: @DINGIRABZU.
- [Audio pipeline refresh](https://github.com/DINGIRABZU/ABZU/pull/194) — owner: @DINGIRABZU.

## Active Tasks
- [Milestone VIII – Sonic Core & Avatar Expression Harmonics](https://github.com/DINGIRABZU/ABZU/issues/208) — owner: @DINGIRABZU (see [milestone_viii_plan.md](milestone_viii_plan.md)).
- [Spiral OS stability](https://github.com/DINGIRABZU/ABZU/issues/210) — owner: ops team.
- [Pydantic v2 migration](https://github.com/DINGIRABZU/ABZU/issues/211) — owner: @DINGIRABZU.
- [FastAPI lifespan migration](https://github.com/DINGIRABZU/ABZU/issues/212) — owner: web team.
- [Optional dependency stubs](https://github.com/DINGIRABZU/ABZU/issues/213) — owner: infra team.

## Planned Releases
- [v0.1](https://github.com/DINGIRABZU/ABZU/milestone/1) – minimal Spiral OS boot sequence and CLI tools (target: Q3 2025).
- [v0.2](https://github.com/DINGIRABZU/ABZU/milestone/2) – avatar console integration and basic RAG pipeline (target: Q4 2025).

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

