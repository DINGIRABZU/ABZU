# The Absolute Pytest

> **Note:** Before writing tests, review [blueprint_spine.md](blueprint_spine.md) and consult the [Code Index](code_index.md) for context.

## Chakra-Aligned Test Layout

Tests mirror the system's chakra map and should live in the matching
directory under `tests/`:

- `tests/root/`
- `tests/sacral/`
- `tests/solar_plexus/`
- `tests/heart/`
- `tests/throat/`
- `tests/third_eye/`
- `tests/crown/`

Place new tests in the directory corresponding to the component's chakra.
Continuous integration enforces **≥90 %** coverage for all active components.

## AI Feedback Loop

- `crown_prompt_orchestrator` reviews Prometheus test metrics after each run.
- When failures are detected it logs remediation suggestions with `log_suggestion` in `corpus_memory_logging`.
- Suggestions are stored alongside other interaction records for later analysis.

## Observability

- `tests/conftest.py` instruments pytest using `prometheus_client`.
- Metrics:
  - `pytest_test_duration_seconds` histogram captures per-test runtimes.
  - `pytest_session_duration_seconds` gauge records total runtime for the test session.
  - `pytest_coverage_percent` gauge stores overall coverage when `--cov` is used.
  - `pytest_test_failures_total` counter increments on failed tests.
- At session end metrics are written to `monitoring/pytest_metrics.prom` for scraping by Prometheus.

Run tests as usual and inspect the metrics file or have Prometheus scrape the path for dashboarding and alerting.

## Coverage Enforcement

- CI runs `pytest --cov` and then `scripts/export_coverage.py` parses the results.
- The step fails if any active component drops below **90%** coverage.
- The `scan-todo-fixme` pre-commit hook blocks commits containing `TODO` or `FIXME` markers.

## Component Tests

Run targeted tests for event structuring, persistence, and multi-track mixing:

```bash
pytest tests/bana/test_event_structurizer.py \
       tests/core/test_memory_physical.py \
       tests/audio/test_mix_tracks.py \
       tests/integration/test_mix_and_store.py \
       --cov=bana/event_structurizer.py \
       --cov=src/core/memory_physical.py \
       --cov=src/audio/mix_tracks.py
```

The coverage gauges in `monitoring/pytest_metrics.prom` should report ≥90% for these modules.

## Dashboard Setup

1. Configure Prometheus to watch `monitoring/pytest_metrics.prom` using a `file_sd_config` target.
2. In Grafana, add panels for:
   - `rate(pytest_test_failures_total[5m])` to track failure spikes.
   - `pytest_session_duration_seconds` to monitor overall runtime.
   - `pytest_coverage_percent` to ensure coverage stays above thresholds.
3. Enable alerts on coverage drops or runtime increases to trigger reviews via `crown_prompt_orchestrator`.

## Ignition Full Stack Test

`tests/ignition/test_full_stack.py` simulates a minimal boot sequence. It stubs
the Crown handshake, initializes the `MemoryStore`, confirms agent channel
availability, and routes an operator command. Use it as a template for
integration-style startup tests when external services are unavailable.

## Failure Analysis

- Pytest writes detailed logs to `logs/pytest.log`.
- Coverage reports live under `htmlcov/` when the `--cov` option is used.
- Archive failures and artifacts for later review:

  ```bash
  tar -czf failure-artifacts.tar.gz logs/ htmlcov/
  ```

  The archive can be shared with AI reviewers alongside entries recorded via
  `corpus_memory_logging.log_test_failure`.

## Lessons from Failure Inventory

The [Failure Inventory](testing/failure_inventory.md) catalogs common issues discovered in the test suite. Apply the following guidelines to avoid repeating them.

### Missing dependency checklist

- Use `importlib.util.find_spec` or `pytest.importorskip` to handle optional libraries.
- Record new packages in `requirements.txt` and `dependency_registry.md`.
- Document installation steps in related module guides.

### Fixture-writing guidelines

- Give fixtures unique module names to avoid import mismatches.
- Isolate side effects with `tmp_path`, `monkeypatch`, or other pytest fixtures.
- Guard external resources with `@pytest.mark.skipif` when prerequisites are absent.

### Library compatibility checks

- Pin library versions when upstream changes break APIs.
- Validate input shapes and dtypes to catch mismatches early.
