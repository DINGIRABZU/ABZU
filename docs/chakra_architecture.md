# Chakra Architecture

This document summarizes the major modules aligned with each chakra layer, their operational state, current quality level, and any known warnings or errors. Semantic version numbers for these layers are tracked in [chakra_versions.json](chakra_versions.json).

| Chakra | Components | State | Quality Level | Known Warnings/Errors |
| --- | --- | --- | --- | --- |
| Root | `server.py`, `INANNA_AI/network_utils/` | I/O and networking foundation | Beta | Network capture may require elevated permissions |
| Sacral | `emotional_state.py`, `emotion_registry.py` | Emotion engine | Beta | Registry entries still growing |
| Solar Plexus | `learning_mutator.py`, `state_transition_engine.py` | Learning and state transitions | Alpha | Mutations can produce unstable states |
| Heart | `voice_avatar_config.yaml`, `vector_memory.py` | Voice avatar configuration and memory storage | Beta | Vector store requires running database |
| Throat | `crown_prompt_orchestrator.py`, `INANNA_AI_AGENT/inanna_ai.py` | Prompt orchestration and agent interface | Beta | None currently |
| Third Eye | `insight_compiler.py`, `SPIRAL_OS/qnl_engine.py`, `seven_dimensional_music.py` | Insight and QNL processing | Experimental | QNL engine emits occasional warnings |
| Crown | `init_crown_agent.py`, `start_spiral_os.py`, `crown_model_launcher.sh` | High-level orchestration | Alpha | Startup scripts assume local model availability |

Additional Nazarick agents expand these layers:
[Bana Bio-Adaptive Narrator](nazarick_agents.md#bana-bio-adaptive-narrator) (Heart),
[AsianGen Creative Engine](nazarick_agents.md#asiangen-creative-engine) (Throat), and
[LandGraph Geo Knowledge](nazarick_agents.md#landgraph-geo-knowledge) (Root).

## Service and Schema Mapping

| Chakra | Modules | Third-party Services | Data Schemas |
| --- | --- | --- | --- |
| Root | `server.py`, `INANNA_AI/network_utils/` | FastAPI, GLM command API | `pcap` captures, `INANNA_AI_AGENT/network_utils_config.json` |
| Sacral | `emotional_state.py`, `emotion_registry.py` | — | `data/emotion_registry.json` |
| Solar Plexus | `learning_mutator.py`, `state_transition_engine.py` | — | `insight_matrix.json` |
| Heart | `voice_avatar_config.yaml`, `vector_memory.py` | Vector database | `voice_avatar_config.yaml`, embedding records |
| Throat | `crown_prompt_orchestrator.py`, `INANNA_AI_AGENT/inanna_ai.py` | LLM APIs | Prompt/response JSON payloads |
| Third Eye | `insight_compiler.py`, `SPIRAL_OS/qnl_engine.py`, `seven_dimensional_music.py` | Audio toolchain | `mirror_thresholds.json`, QNL glyph sequences |
| Crown | `init_crown_agent.py`, `start_spiral_os.py`, `crown_model_launcher.sh` | Model runtime, container services | `pipeline` YAML, `ritual_profile.json` |

## Chakra Cycle Engine

The chakra cycle engine paces each layer with a timed heartbeat. Every tick
broadcasts a pulse across Root through Crown and gathers their responses to
keep the stack synchronized.

### Heartbeat Ratios

Each layer reports its beat relative to the engine’s tick. Deviations beyond
the expected 1 :1 rhythm generate alignment events, which surface in the
[System Blueprint](system_blueprint.md#chakra-cycle-engine).

### Alignment Events

Alignment events are logged and echoed into the architecture map so operators
can correlate misfires with service health. The
[Blueprint Spine](blueprint_spine.md#heartbeat-propagation-and-self-healing)
illustrates the propagation path.

### Silent Chakra Remediation

If a layer fails to answer a heartbeat, the engine marks it silent and
requests remediation from [NAZARICK agents](nazarick_agents.md). Those
servants reinitialize the dormant chakra following the self-healing loop
outlined in the [Self-Healing Manifesto](self_healing_manifesto.md).
