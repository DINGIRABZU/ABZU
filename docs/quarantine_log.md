# Quarantine Log

Failed components are moved to the `quarantine/` directory and recorded below.
Remote agents may also submit diagnostic information for quarantined
components; these entries appear in the log with an `diagnostic` action.

## Restoring components

To reinstate a component once it is fixed:

1. Remove its JSON file from the `quarantine/` directory.
2. Append a `resolved` entry in this log with any relevant notes.
3. Invoke `reactivate_component` with `verified=True` to record a manual or
   automated reactivation.

| Timestamp (UTC) | Component | Action | Details |
|-----------------|-----------|--------|---------|
