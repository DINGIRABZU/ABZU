# Voice Aura FX

`voice_aura.py` applies subtle reverb and delay based on the current emotion.
Each emotion maps to a simple preset:

| Emotion  | Reverb | Delay |
|---------|-------|------|
| neutral | 20    | 100  |
| joy     | 30    | 80   |
| excited | 25    | 50   |
| calm    | 50    | 150  |
| sad     | 60    | 200  |
| fear    | 70    | 120  |
| stress  | 40    | 60   |

The module checks if the `sox` command is available to process effects.
If not, it falls back to `pydub`.  Optional RAVE or NSynth checkpoints can
morph the timbre via `dsp_engine.rave_morph` or `nsynth_interpolate`.

