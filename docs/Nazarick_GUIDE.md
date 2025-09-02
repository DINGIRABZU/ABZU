# Nazarick Guide

## Vision
Nazarick hosts specialized servant agents aligned to chakra layers and coordinated by RAZAR and Crown.

## Architecture
- Agents registered in `agents/nazarick/agent_registry.json`.
- `launch_servants.sh` starts individual servants.
- Logs written to `logs/nazarick_startup.json`.

## Deployment
```bash
./launch_servants.sh orchestration_master
```
Set `NAZARICK_ENV` for configuration profile and `NAZARICK_LOG_DIR` for log paths.

## Configuration Schemas
- `agents/nazarick/agent_registry.json` — metadata for servants.

## Example Runs
```bash
python start_dev_agents.py --all
```

## Cross-Links
- [RAZAR Guide](RAZAR_GUIDE.md)
- [Crown Guide](Crown_GUIDE.md)
- [Narrative Engine Guide](narrative_engine_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2025-10-17 | Initial servant registry and deployment commands. |
