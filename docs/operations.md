# Operations

## RAZAR startup

Launch the RAZAR runtime manager before any other component to prepare the
environment and start services in priority order:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

The orchestrator builds or validates the dedicated virtual environment and
records the last successful component in a `.state` file. Monitor the
`/health` endpoint to confirm the environment hash and heartbeat.

Use ``razar.mission_logger`` to record progress as components start (see
[logging guidelines](logging_guidelines.md) for event types and examples):

```bash
python -m razar.mission_logger log gateway success
python -m razar.mission_logger summary
```

Entries are stored in ``logs/razar.log``. The ``summary`` command prints the
last successful component and lists pending tasks based on the most recent
status for each component. For a full chronological view, run ``razar
timeline`` to reconstruct the mission sequence.

If RAZAR cannot restart a component, rebuild the virtual environment and rerun
the manager. Removing the `.state` file forces a full restart sequence.

## RAZAR failure runbook

1. **Summarize status**
   ```bash
   python -m razar.mission_logger summary
   ```
   Review `logs/razar.log` for the last successful component.
2. **Reset state**
   Remove `config/razar_config.state` to re-run the full sequence.
3. **Rebuild environment**
   ```bash
   python -m razar.environment_builder --config razar_env.yaml
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```
4. **Quarantine persistent failures**
   ```python
   from razar import quarantine_manager as qm
   qm.quarantine_component({"name": "gateway"}, "health check failed")
   ```

## Quarantine management

- Quarantined components are written to the `quarantine/` directory and logged
  in [quarantine_log.md](quarantine_log.md).
- To restore a component, remove its JSON file from `quarantine/` and record a
  resolved entry:
  ```python
  from razar import quarantine_manager as qm
  qm.resolve_component("gateway", note="reconfigured credentials")
  ```
  Append notes to `docs/quarantine_log.md` for auditability.

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

## Service monitoring

Use `monitoring/watchdog.py` to track resource usage of critical processes.
The script relies on `psutil` and exposes Prometheus metrics for CPU, memory
and open file descriptors:

```bash
python monitoring/watchdog.py
```

Edit the `SERVICES` dictionary in the script to list the process names or
command line fragments to monitor. Metrics are published on port `9100` by
default and can be scraped with Prometheus. To verify locally:

```bash
curl http://localhost:9100/metrics
```

### Troubleshooting

- Ensure `psutil` and `prometheus_client` are installed.
- Check that the monitored process names match running services.
- If metrics are missing, confirm the watchdog is running and that port `9100`
  is reachable.
