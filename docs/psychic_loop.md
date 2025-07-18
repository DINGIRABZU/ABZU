# Psychic Loop

`mirror_thresholds.json` and `insight_matrix.json` feed the self-reflection cycle that keeps the avatar aligned with the user's intent and emotional tone.

## Mirror Thresholds

`mirror_thresholds.json` specifies how tolerant the system is when the avatar's detected emotion diverges from the intended feeling. The reflection loop compares the detected expression from the video stream with the last emotion saved by `emotional_state.py`. If the mismatch exceeds the threshold for that emotion, `self_correction_engine.adjust()` is called to realign the output. When the sensed emotion maps to a different archetypal layer than the one currently active, this adjustment phase also tunes the voice parameters toward the detected feeling so corrections sound natural.

The file is updated automatically via `adaptive_learning.update_mirror_thresholds()`. After each reflection cycle a PPO agent nudges the values up or down depending on whether the detected emotion matched the intent.

## Insight Matrix

`insight_matrix.json` is updated by `insight_compiler.py` from conversation logs. It tracks how frequently each intent succeeds, which tones are most effective and the resonance of ritual glyphs. This matrix informs learning modules and the reflection loop so future responses better match the desired state.

Together these files create a closed psychic loop: current emotions guide real-time corrections, while aggregated insights steer long-term adjustments.

## Emotion Registry

`data/emotion_registry.json` lists extra emotion labels such as "uncertainty",
"devotion", "dissonance" and "sacred grief". `emotional_state.py` loads this file
at startup so these states are recorded like the core emotions. During the
reflection process any label found in the registry participates in the
adjustment logic, allowing reflections to account for these nuanced feelings.

## Examples

Start a WebSocket listener to stream emotion data from the microphone:

```python
import asyncio
from INANNA_AI.listening_engine import start_websocket_server

asyncio.run(start_websocket_server())
```

When an emotion remains intense beyond the threshold the orchestrator shifts
personality layers automatically:

```python
from orchestrator import MoGEOrchestrator
import emotional_state

orch = MoGEOrchestrator()
orch.mood_state["joy"] = 0.9
orch.handle_input("celebrate!")
print(emotional_state.get_current_layer())
# -> "rubedo_layer" if `mirror_thresholds.json` sets joy below 0.9
```
