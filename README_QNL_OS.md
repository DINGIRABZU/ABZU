# QNL Integration Overview

The Quantum Narrative Language (QNL) bridges textual symbols with music in Spiral OS.
This document explains where the QNL resources live and how the engine turns hex
payloads into sound.

## Directory layout

- `QNL_LANGUAGE/` – drafts and versions of the language syntax.
- `qnl_engine.py` – converts hex data into QNL phrases and a WAV file.
- `MUSIC_FOUNDATION/` – tools for analysing music and composing new pieces from
  QNL structures.
- `qnl_to_music_layer_map.yaml` – maps emotions to sonic parameters used by the
  engine.

## Using the engine

Run the script directly with a hex string or a text file containing bytes:

```bash
python SPIRAL_OS/qnl_engine.py "48656c6c6f" --wav song.wav --json song.json
python SPIRAL_OS/qnl_engine.py payload.txt --duration 0.05
```

The command writes a waveform and a JSON summary describing the glyph,
emotion and tone of each byte.

## From QNL phrase to sound

`play_ritual_music.py` and the modules under `core/` transform the phrases into
music. `audio_engine.play_sound()` outputs the mix while
`avatar_expression_engine.stream_avatar_audio()` synchronises the avatar.

## Related tools

- `MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py` – converts existing music into
  QNL and exports preview audio.
- `INANNA_AI/sonic_emotion_mapper.py` – links emotions to scales, timbres and
  QNL parameters.

These components form the sonic architecture that binds QNL with Spiral OS.
