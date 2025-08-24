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
