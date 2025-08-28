# Operations

## RAZAR startup

Launch the RAZAR runtime manager before any other component to prepare the
environment and start services in priority order:

```bash
python -m agents.razar.runtime_manager config/razar_config.yaml
```

The orchestrator builds or validates the dedicated virtual environment using
`razar_env.yaml` and records the last successful component in
`logs/razar_state.json`. Monitor the `/health` endpoint to confirm the
environment hash and heartbeat. Failed components are automatically moved to
`quarantine/`, classified by `razar.issue_analyzer`, and logged in
`docs/quarantine_log.md` with their issue type and suggested fix.

Use ``razar.mission_logger`` to record progress as components start, report
health results, enter quarantine and receive patches (see
[logging guidelines](logging_guidelines.md) for event types and examples):

```bash
python -m razar.mission_logger log gateway success --event start
python -m razar.mission_logger summary
```

Entries are stored as JSON lines in ``logs/razar.log``. The ``summary``
command prints the last successful component and lists pending tasks based on
the most recent status for each component. The ``razar timeline`` CLI parses
these entries to reconstruct the mission sequence.

For a real-time snapshot of boot progress and component priorities, launch the
status dashboard:

```bash
python -m razar.status_dashboard
```

The dashboard also links to quarantine logs and the boot history.

For protocol details of the lifecycle bus and automated recovery flow, see
the [RAZAR Agent guide](RAZAR_AGENT.md#lifecycle-bus-and-recovery-protocol).

If RAZAR cannot restart a component, rebuild the virtual environment and rerun
the manager. Removing `logs/razar_state.json` forces a full restart sequence.

## RAZAR failure runbook

1. **Summarize status**
   ```bash
   python -m razar.mission_logger summary
   ```
   Review `logs/razar.log` for the last successful component.
2. **Reset state**
   Remove `logs/razar_state.json` to re-run the full sequence.
3. **Rebuild environment**
   ```bash
   python -m razar.environment_builder --config razar_env.yaml
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```
4. **Review quarantine**
   Inspect `quarantine/` and `docs/quarantine_log.md` for modules isolated by
   the runtime manager. Each entry includes an issue type to aid triage.
   After applying fixes, return the module to its original path and optionally
   record a resolved entry with `quarantine_manager.resolve_component`.

## Quarantine management

- Quarantined modules are written to the `quarantine/` directory and logged in
  [quarantine_log.md](quarantine_log.md) with their issue type and suggested fix.
- To restore a module, return its file from `quarantine/`, remove any metadata
  JSON, and record a resolved entry:
  ```python
  from razar import quarantine_manager as qm
  qm.resolve_component("gateway", note="reconfigured credentials")
  ```
  Append notes to `docs/quarantine_log.md` for auditability.

## Downtime and patching

When CROWN flags a component for maintenance it sends a downtime request during
the mission brief handshake. RAZAR coordinates the following sequence
automatically via `razar.recovery_manager`:

1. **Shutdown** – `request_shutdown(name)` writes an audit entry under
   `recovery_state/` and instructs the component to stop.
2. **Patch** – `apply_patch(name, info)` saves patch metadata so operators can
   review what was applied.
3. **Resume** – `resume(name)` records that the component has been restarted.

Operators can inspect the JSON files in `recovery_state/` to confirm that the
cycle completed and to gather details about the applied patch.

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
