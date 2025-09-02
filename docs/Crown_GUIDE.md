# Crown Guide

## Vision
Crown routes operator commands to servant models and maintains dialogue context.

## Architecture
- Console accepts operator input.
- Crown Agent contacts GLM and servant models.
- State Transition Engine coordinates responses.

## Deployment
```bash
python start_crown_console.py
```
Requires reachable GLM endpoints and servant model URLs.

## Configuration Schemas
- `crown_config/INANNA_CORE.yaml` — GLM and memory settings.
- `SERVANT_MODELS` env var — maps servant names to URLs.

## Example Runs
```bash
curl -X POST localhost:8000/operator/command -d '{"command":"status"}'
```

## Cross-Links
- [RAZAR Guide](RAZAR_GUIDE.md)
- [System Blueprint](system_blueprint.md)
- [Operator Interface Guide](operator_interface_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.5.0 | 2025-10-25 | Added deployment walkthrough and mission brief examples. |
| 0.1.0 | 2025-08-28 | Initial architecture outline. |
