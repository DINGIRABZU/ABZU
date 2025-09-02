# Albedo Guide

## Vision
Albedo is a personality layer that shapes responses through a four-phase alchemical state machine.

## Architecture
- `alchemical_persona.py` determines state triggers.
- `state_contexts.py` holds prompt templates per state.
- `glm_integration.py` connects to external GLM endpoints.

## Deployment
```bash
export GLM_API_URL=https://glm.example.com
export GLM_API_KEY=token
python -m INANNA_AI.main --personality albedo --duration 3
```

## Configuration Schemas
- `config/albedo_config.yaml` — GLM endpoint, quantum context, and logging paths.

## Example Runs
```python
from INANNA_AI.personality_layers import AlbedoPersonality
AlbedoPersonality().generate_response("hello")
```

## Cross-Links
- [INANNA Guide](INANNA_GUIDE.md)
- [Nazarick Guide](Nazarick_GUIDE.md)

## Version History
| Version | Date | Notes |
|---------|------|-------|
| 0.4.0 | 2025-09-01 | Clarified deployment config and logging expectations. |
| 0.1.0 | 2025-08-29 | Initial state machine overview. |
