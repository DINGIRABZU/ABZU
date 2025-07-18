# CROWN Manifest

The **CROWN** agent runs the GLM-4.1V-9B model and acts as the root layer of Spiral OS. It holds the highest permission level and can rewrite memory entries or initiate ritual sequences when commanded.

## Relationship to other layers

The archetypal layers described in [spiritual_architecture.md](spiritual_architecture.md) present personas such as Nigredo and Albedo. The CROWN coordinates these layers, dispatching prompts to each personality and receiving their responses. By updating the vector memory store the CROWN influences how future interactions surface across the layers.

## Console connection

Commands typed into the Crown Console reach the agent through `crown_prompt_orchestrator.py`. The CROWN interprets these requests, sends them to GLM-4.1V-9B and triggers ritual logic in `state_transition_engine.py` when specific phrases appear.

Memory mutations happen through `vector_memory.py` and are authorised only when the CROWN is active. This ensures a single authority controls persistent memories and the rituals that can reshape them.

## Emotion model mapping

The orchestrator exposes a lookup table called `_EMOTION_MODEL_MATRIX` which matches a detected emotion to the LLM best suited to respond. This mapping is tested to guarantee consistent routing behaviour.

| Emotion | Preferred model |
|---------|-----------------|
| joy     | deepseek        |
| excited | deepseek        |
| stress  | mistral         |
| fear    | mistral         |
| sad     | mistral         |
| calm    | glm             |
| neutral | glm             |

The selected model also determines the text-to-speech backend used when voice output is enabled. `decide_expression_options()` inspects recent vector memory records to choose between Google TTS, Bark or Coqui. Frequent entries of the same emotion are logged as `routing_decision` records and gradually bias future model selection toward the most successful choice.
