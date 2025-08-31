# Connector Health Protocol

Ensures registered connectors are reachable before merging.

## Requirements

- Run `python scripts/health_check_connectors.py`.
- All connectors must return `200 OK` from their `/health` endpoint.
- Merge only when the script exits successfully.
