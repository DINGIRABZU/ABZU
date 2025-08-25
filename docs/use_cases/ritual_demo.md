# Ritual Demo

This walkthrough demonstrates the small ritual sample included with the
repository. The `examples/ritual_demo.py` script performs three actions:

1. Sets the current emotion with `emotional_state.set_last_emotion`.
2. Plays a bundled tone from `examples/assets/ritual_tone.wav`.
3. Logs a dummy insight using `memory.spiral_cortex.log_insight`.

## Running the demo

```bash
python examples/ritual_demo.py
```

Audio playback uses the optional `simpleaudio` package. If the library is not
available the script skips playback and continues. The logged insight is stored
in `data/spiral_cortex_memory.jsonl`.

Sample assets for the demo are located under `examples/assets/`.
