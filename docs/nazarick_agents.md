# Nazarick Agents

This guide summarizes core agents within ABZU's Nazarick system. Each agent aligns with a chakra layer, defines its memory scope, and relies on key external libraries. Implementation stubs are linked for future development.

| Agent | Role | Chakra | Memory Scope | External Libraries | Stub |
| --- | --- | --- | --- | --- | --- |
| Orchestration Master | High-level orchestration and launch control | Crown | `pipeline` YAML, `ritual_profile.json` | Model runtime, container services | [orchestration_master.py](../orchestration_master.py) |
| Prompt Orchestrator | Prompt routing and agent interface | Throat | Prompt/response JSON payloads | LLM APIs | [crown_prompt_orchestrator.py](../crown_prompt_orchestrator.py) |
| QNL Engine | Insight and QNL processing | Third Eye | `mirror_thresholds.json`, QNL glyph sequences | Audio toolchain | [SPIRAL_OS/qnl_engine.py](../SPIRAL_OS/qnl_engine.py) |
| Memory Scribe | Voice avatar configuration and memory storage | Heart | `voice_avatar_config.yaml`, embedding records | Vector database | [memory_scribe.py](../memory_scribe.py) |

These agents draw from the chakra structure outlined in the [Developer Onboarding guide](developer_onboarding.md) and [Chakra Architecture](chakra_architecture.md).

