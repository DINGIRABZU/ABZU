# Operations

## Dependency audits

Use `tools/dependency_audit.py` to ensure installed packages match the pinned
versions listed in `pyproject.toml`.

### Daily cron example

Run the audit every day at 03:00 and capture the output in a log file:

```
0 3 * * * /usr/bin/python /path/to/repo/tools/dependency_audit.py >> /path/to/repo/logs/dependency_audit.log 2>&1
```

The script returns a non-zero exit code when mismatches or missing packages are
detected, allowing cron to report failures.

## Model download verification

Model downloads performed with `download_models.py` now include checksum
validation, retry logic and write detailed results to
`logs/model_audit.log`.

## Triage failing tests

Use the development agents to investigate failing tests. Run `start_dev_agents.py`
with `--triage` and one or more pytest paths:

```
python start_dev_agents.py --triage tests/test_example.py
```

The script executes the specified suites and writes the full pytest output to
`logs/triage_<timestamp>.log`. When failures occur it launches the
planner/coder/reviewer agents to suggest fixes. Interactions from each triage
run are stored under `data/triage_sessions/` for later review.
