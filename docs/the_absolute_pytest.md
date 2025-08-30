# The Absolute Pytest

## AI Feedback Loop

- `crown_prompt_orchestrator` reviews Prometheus test metrics after each run.
- When failures are detected it logs remediation suggestions with `log_suggestion` in `corpus_memory_logging`.
- Suggestions are stored alongside other interaction records for later analysis.

## Observability

- `tests/conftest.py` instruments pytest using `prometheus_client`.
- Metrics:
  - `pytest_test_duration_seconds` histogram captures per-test runtimes.
  - `pytest_test_failures_total` counter increments on failed tests.
- At session end metrics are written to `monitoring/pytest_metrics.prom` for scraping by Prometheus.

Run tests as usual and inspect the metrics file or have Prometheus scrape the path for dashboarding and alerting.
