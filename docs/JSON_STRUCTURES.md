# JSON Structures and Invocations

This page describes the small JSON files used by Spiral OS and how to trigger
registered invocations.

## `data/emotion_state.json`

```
{
  "current_layer": null,
  "last_emotion": null,
  "resonance_level": 0.0,
  "preferred_expression_channel": "text",
  "resonance_pairs": [],
  "soul_state": null
}
```

The orchestrator updates this file through `emotional_state.py` whenever a new
emotion is detected.

## `ritual_profile.json`

```
{
  "☉": {
    "joy": ["open portal", "weave sound"],
    "sadness": ["invoke remembrance"]
  },
  "☾": {
    "calm": ["merge forms"],
    "anger": ["conjure fire"]
  }
}
```

`task_profiling.ritual_action_sequence()` expands a symbol and emotion pair to a
list of ritual actions.

## Example invocation registration

```
import invocation_engine

def open_portal(symbols, emotion, orch=None):
    return f"Portal opened with {symbols}"

invocation_engine.register_invocation("∴⟐+🜂", "joy", open_portal)
invocation_engine.invoke("∴⟐ + 🜂 [joy]")
```

This pattern-based engine matches the glyphs and optional emotion to dispatch
the callback.
