# Quarantine Log

Failed modules are moved to the `quarantine/` directory and categorized by
issue type. Each entry below includes a suggested fix to guide restoration.
Remote agents may submit additional diagnostic information using
`quarantine_manager.record_diagnostics`.

## Restoring modules

To reinstate a module once it is fixed:

1. Return the file from `quarantine/` to its original location.
2. Append a `resolved` entry in this log with any relevant notes.
3. Invoke `reactivate_component` with `verified=True` to record a manual or
   automated reactivation.

| Timestamp (UTC) | Module | Issue Type | Suggested Fix |
|-----------------|--------|------------|---------------|
