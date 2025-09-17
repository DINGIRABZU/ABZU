# Project Status

![Coverage](../coverage.svg)

The badge above is generated via `scripts/export_coverage.py`, which runs
`coverage-badge` after tests complete.

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
pytest --maxfail=1 --cov --cov-fail-under=90 -q \
  tests/test_start_spiral_os.py \
  tests/test_spiral_os.py \
  tests/integration/test_razar_failover.py \
  tests/test_spiral_memory.py \
  tests/test_vector_memory.py \
  tests/test_vector_memory_extensions.py \
  tests/test_vector_memory_persistence.py \
  tests/test_spiral_vector_db.py
```

Stage A rehearsals now exercise the Spiral OS boot entry points alongside Spiral memory and vector regression tests. Runs are expected to meet the ≥90 % coverage bar reflected in `coverage.svg`; failures block promotion from the gate.

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
- v0.1 – minimal Spiral OS boot sequence and CLI tools (target: Q3 2025). **Status:** Charter baseline approved in [alpha_v0_1_charter.md](alpha_v0_1_charter.md); subsystem execution tracked through the [Alpha v0.1 execution plan](roadmap.md#alpha-v01-execution-plan). Stage snapshots: **Stage A** focuses on Alpha gate automation readiness, **Stage B** locks subsystem hardening for sonic core, memory, and connectors, and **Stage C** synchronizes exit checklist, demo assets, and readiness signals. See the [Milestone Stages overview](roadmap.md#milestone-stages) for task-level detail. Reference the [Python Alpha Squad dossier](onboarding/python_alpha_squad.md) for RAZAR boot ownership and daily reliability rituals feeding that plan.
- v0.2 – avatar console integration and basic RAG pipeline (target: Q4 2025). **Status:** Backlog shaping pending Alpha v0.1 exit criteria.

## Alpha v0.1 Readiness Gate
- Workflow defined in [docs/releases/alpha_v0_1_workflow.md](releases/alpha_v0_1_workflow.md) covering packaging, mandatory health checks, and acceptance tests.
- Automation available through `scripts/run_alpha_gate.sh` with optional connector sweeps and pytest argument passthrough.
- GitHub Actions [`Alpha Gate`](../.github/workflows/alpha_gate.yml) runs on pushes to `main`, a weekly Monday 06:00 UTC schedule, and on-demand dispatch to gate release candidates. The job restores cached `dist/` wheels, starts mock connector probes, and publishes `logs/alpha_gate/` and build artifacts for review. Successful runs append a stamped entry to `CHANGELOG.md` inside the log bundle for audit trails.
- Dry runs validate build artifact generation (`python -m build --wheel`) and Spiral OS / RAZAR acceptance coverage ahead of staging promotion. The same steps are codified in [`deployment/pipelines/alpha_gate.yml`](../deployment/pipelines/alpha_gate.yml) for local `spiral-os pipeline deploy` rehearsal.
- Doctrine drift is now gated by `python scripts/check_identity_sync.py`. If the check reports that `data/identity.json` predates updates to the mission, persona, Absolute Protocol, ABZU blueprint, or awakening overview doctrine, rerun `python scripts/refresh_crown_identity.py --use-stub` before continuing the gate.

## Deprecation Roadmap

- **Pydantic field aliases** – migrate remaining models away from deprecated
  `Field` parameters and switch to explicit `alias` and
  `populate_by_name` configuration.
- **FastAPI lifespan** – replace `@app.on_event` startup and shutdown hooks
  with the `lifespan` context manager before the old API is removed.

## Getting Started

See [README.md](../README.md) for installation instructions and additional documentation links. Contributors are encouraged to run tests frequently and document any new modules under `docs/`.

