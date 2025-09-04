# Error Registry

This registry tracks recurring issues observed during component startup and operation. Each entry documents symptoms and the steps that resolved the problem.

Errors detected in logs can be appended via [`scripts/update_error_index.py`](../scripts/update_error_index.py).

| Issue | Symptoms | Resolution |
| --- | --- | --- |
| network-timeout | Component cannot reach an external service and raises repeated timeout errors. | Verify network connectivity and DNS settings, then retry once the service is reachable. |
| missing-dependency | Startup fails with an `ImportError` indicating a module is missing. | Install the required package with `pip install <package>` and restart the component. |
| config-mismatch | Component rejects configuration files due to unexpected fields or schema changes. | Update the configuration to the latest schema and reload the component. |

Add new entries as additional patterns emerge.

## Logged Errors

- CROWN_WS_URL not set
- ERROR: usage: pytest [options] [file_or_dir] [file_or_dir] [...]
- pytest: error: unrecognized arguments: --cov=src --cov=agents --cov-fail-under=90
- RAZAR: Initial ImportError - missing `run_validated_task` in patched `agents.guardian`; added stub to satisfy dependency.
