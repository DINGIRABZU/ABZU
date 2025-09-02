# Quarantine Log

Failed components are moved to the `quarantine/` directory and recorded below.

## Restoring components

To reinstate a component once it is fixed:

1. Remove its JSON file from the `quarantine/` directory.
2. Append a `resolved` entry in this log with any relevant notes.

| Timestamp (UTC) | Component | Action | Details |
|-----------------|-----------|--------|---------|
| 2025-09-02T22:06:32Z | boot_orchestrator | quarantined | dependency: circular import prevents import of run_validated_task from agents.guardian; refactor imports to break cycle |

