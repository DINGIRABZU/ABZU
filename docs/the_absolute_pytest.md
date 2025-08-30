# The Absolute Pytest

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

## Dashboard Setup

1. Configure Prometheus to watch `monitoring/pytest_metrics.prom` using a `file_sd_config` target.
2. In Grafana, add panels for:
   - `rate(pytest_test_failures_total[5m])` to track failure spikes.
   - `pytest_session_duration_seconds` to monitor overall runtime.
   - `pytest_coverage_percent` to ensure coverage stays above thresholds.
3. Enable alerts on coverage drops or runtime increases to trigger reviews via `crown_prompt_orchestrator`.

## Failure Analysis

- Pytest writes detailed logs to `logs/pytest.log`.
- Coverage reports live under `htmlcov/` when the `--cov` option is used.
- Archive failures and artifacts for later review:

  ```bash
  tar -czf failure-artifacts.tar.gz logs/ htmlcov/
  ```

  The archive can be shared with AI reviewers alongside entries recorded via
  `corpus_memory_logging.log_test_failure`.
