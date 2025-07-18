# Emotional Memory Matrix

The emotional memory matrix interconnects the various JSON files that store conversation history and affect metrics. Together they guide how Spiral OS reacts to changing moods and which language model should respond.

## Memory nodes

- `insight_matrix.json` &ndash; aggregates success counts, tone resonance and ritual glyph usage.
- `intent_matrix.json` &ndash; maps phrases to actions and stores preferred emotional tones.
- `mirror_thresholds.json` &ndash; defines how far the detected mood may drift before the reflection loop performs a self‑correction.
- `emotion_registry.json` &ndash; lists recognised emotions beyond the standard set so nuanced states can be logged.

Each node contributes to the ongoing reflection cycle described in [psychic_loop.md](psychic_loop.md). Entries contain timestamps and resonance values that decay over time to keep responses fresh.

## Affect scoring

`insight_compiler.py` updates the insight matrix from chat logs. It calculates a success rate for each intent and multiplies it by the recorded resonance level:

```
affect_score = success_rate * resonance_level
```

Higher scores increase the likelihood that a tone or memory snippet surfaces in future prompts. This weighting also influences which archetypal layer becomes active when emotional intensity spikes.

## Crown decider

The crown agent consults `crown_decider.py` when a request arrives. The module reviews emotional memory logs for each servant model and compares their average resonance and success rate for the detected task type. The highest scoring servant is chosen if at least three matching interactions are logged; otherwise the main GLM model is used.

By selecting a servant model that matches the emotional context, the crown decider keeps responses aligned with the user&rsquo;s state while offloading specialised prompts to the most capable LLM.

