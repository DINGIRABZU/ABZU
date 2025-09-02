# Operator Interface Guide

## Vision
Defines REST endpoints that let operators control Crown and RAZAR.

## Architecture
- `/operator/command` forwards actions to RAZAR.
- `/operator/upload` sends files and metadata.
- All requests require Bearer tokens issued by Crown.

## Deployment
Expose the API via the Crown console and export `OPERATOR_TOKEN` for authentication.

## Configuration Schemas
- JSON body: `{ "action": "status", "parameters": {} }`.

## Example Runs
```bash
curl -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -d '{"command":"status"}' \
  localhost:8000/operator/command
```

## Cross-Links
- [Crown Guide](Crown_GUIDE.md)
- [RAZAR Guide](RAZAR_GUIDE.md)
- [Narrative Engine Guide](narrative_engine_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-10-17 | Initial operator endpoints. |
