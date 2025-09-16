# Chakra Status

This document tracks capabilities, limitations, and planned evolutions for each chakra layer.
Update after every milestone completion.
Semantic versions are maintained in [chakra_versions.json](chakra_versions.json).

| Chakra | Version | Capabilities | Limitations | Planned Evolutions | Modules |
| --- | --- | --- | --- | --- | --- |
| Root | 1.0.0 | I/O and networking foundation with basic system monitoring | Network capture may require elevated permissions | Schedule automated captures and improve security hardening | [`server.py`](../server.py), [`INANNA_AI/network_utils`](../INANNA_AI/network_utils) |
| Sacral | 1.0.0 | Emotion engine tracking and updating emotional state | Emotion registry remains limited | Expand emotion taxonomy and integrate feedback learning | [`emotional_state.py`](../emotional_state.py), [`emotion_registry.py`](../emotion_registry.py) |
| Solar Plexus | 1.0.0 | Learning and state transition management | Mutations can produce unstable states | Introduce stability checks and rollback mechanisms; defer richer “Mutator Evolution” capability until after first functional Alpha | [`learning_mutator.py`](../learning_mutator.py), [`state_transition_engine.py`](../state_transition_engine.py) |
| Heart | 1.0.0 | Voice avatar configuration and vector memory storage | Requires running vector database | Add distributed memory and refine avatar tuning | [`voice_avatar_config.yaml`](../voice_avatar_config.yaml), [`vector_memory.py`](../vector_memory.py) |
| Throat | 1.0.0 | Prompt orchestration and agent interface | Minimal routing metrics | Implement advanced routing metrics and unified prompt templates | [`crown_prompt_orchestrator.py`](../crown_prompt_orchestrator.py), [`INANNA_AI_AGENT/inanna_ai.py`](../INANNA_AI_AGENT/inanna_ai.py) |
| Third Eye | 1.0.1 | Insight compilation, QNL processing, biosignal narrative generation | QNL engine emits occasional warnings | Improve symbolic parser and validate QNL output | [`insight_compiler.py`](../insight_compiler.py), [`SPIRAL_OS/qnl_engine.py`](../SPIRAL_OS/qnl_engine.py), [`seven_dimensional_music.py`](../seven_dimensional_music.py), [`agents/bana/bio_adaptive_narrator.py`](../agents/bana/bio_adaptive_narrator.py) |
| Crown | 1.0.0 | High-level orchestration of system start-up and crown agent | Assumes local model availability | Add remote model provisioning and boot diagnostics | [`init_crown_agent.py`](../init_crown_agent.py), [`start_spiral_os.py`](../start_spiral_os.py), [`crown_model_launcher.sh`](../crown_model_launcher.sh) |

