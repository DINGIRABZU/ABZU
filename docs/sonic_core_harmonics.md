# Sonic Core Harmonics

The Sonic Core layers audio synthesis and expression modules on top of Spiral OS. It transforms QNL phrases into audible waveforms and synchronises the avatar with every beat.

## Modules

- `audio_engine.py` – plays WAV files and loops samples via an `AudioSegment` abstraction. By default it uses a lightweight NumPy backend. Set `AUDIO_BACKEND=pydub` when `pydub` and the `ffmpeg` binary are installed to enable the full backend. `play_sound(path, loop=False, loops=None)` repeats the sample `loops` times or indefinitely when `loop=True`.
- `MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py` – converts music into QNL structures and exports preview audio.
- `MUSIC_FOUNDATION/seven_plane_analyzer.py` – maps musical features to seven metaphysical planes.
- `core/avatar_expression_engine.py` – streams avatar frames in time with audio playback.
- `core/facial_expression_controller.py` – applies emotion colours and mouth movements.
- `core/video_engine.py` – base avatar renderer.
- `INANNA_AI/sonic_emotion_mapper.py` – links emotions to scale, timbre, harmonics and QNL parameters. `emotional_tone_palette.yaml` now lists all Jungian archetypes.

## Required Libraries

- `librosa` for audio analysis
- `soundfile` for WAV I/O
- `opensmile` for emotion detection
- `EmotiVoice` and `sounddevice` for optional voice cloning
- Optional: `pydub` and the `ffmpeg` binary for the full `AudioSegment` backend. Set `AUDIO_BACKEND=pydub` when both are available.

## From QNL Phrase to Sound

1. `inanna_music_COMPOSER_ai.py` or `qnl_utils.generate_qnl_structure` produces QNL phrases.
2. `play_ritual_music.py` composes a short melody from these phrases and writes `ritual.wav`.
3. `audio_engine.play_sound()` outputs the file while `avatar_expression_engine.stream_avatar_audio()` yields frames. When the optional `wav2lip` package is installed the lips are synced precisely; otherwise a basic mouth overlay is used.

## Quick Test

```bash
python play_ritual_music.py --emotion joy --output ritual.wav
```

```python
from pathlib import Path
from core.avatar_expression_engine import stream_avatar_audio

# Falls back to a simple overlay when `wav2lip` is not installed
for _ in stream_avatar_audio(Path("ritual.wav")):
    pass
```

### Runtime mixes

Overlay loops no longer live in `MUSIC_FOUNDATION/sound_assets`. Instead small
base64 snippets are embedded directly in `play_ritual_music.py`. When a mix for
an archetype is missing, the script generates a short sine tone on the fly.
`audio_engine.get_asset_path()` follows the same approach for sound effects,
synthesizing a temporary file if the requested asset does not exist.

### Archetype palette

`emotional_tone_palette.yaml` assigns a scale, instrument list and harmonics
profile to every archetype. The palette now includes the Jungian voices
`Jester`, `Warrior`, `Orphan`, `Caregiver`, `Hero`, `Sage` and
`Everyman` in addition to the four alchemical states.

### Emotion listener example

Use `INANNA_AI.audio_emotion_listener.listen_for_emotion` to capture a short recording and update the shared emotional state:

```python
from INANNA_AI.audio_emotion_listener import listen_for_emotion

info = listen_for_emotion(2.0)
print(info["emotion"])
```

### Voice cloning with EmotiVoice

Install the optional dependencies and record a reference sample:

```bash
pip install emotivoice sounddevice soundfile
python cli/console_interface.py --speak
/clone-voice "The clone is alive."
```

The command captures a short microphone sample, generates a confirmation
phrase and stores the voice for later synthesis.

#### Ethical guidelines

- Clone only your own voice or with explicit permission from the owner.
- Inform listeners that audio was generated and avoid deceptive usage.
- Comply with local laws and respect privacy when storing or sharing samples.
