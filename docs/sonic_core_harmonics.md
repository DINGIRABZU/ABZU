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

## Optional components and fallback behaviour

Stage B rehearsals often operate with a reduced toolchain. Track which optional
packages are missing so the resulting artefacts can be interpreted correctly.

| Component | Sonic Core role | Behaviour when missing | Primary mitigation |
| --- | --- | --- | --- |
| SadTalker | Drives the 3‑D lip-sync pipeline during avatar playback. | Falls back to procedural frames without SadTalker mouth cues. | Install the SadTalker extra or document the simplified render. 【F:docs/optional_dependency_fallbacks.md†L7-L14】 |
| wav2lip | Aligns lip motion with generated speech. | Uses amplitude overlays only, desynchronising lip motion. | Pin the `wav2lip` extra or record the degraded sync in rehearsal notes. 【F:docs/optional_dependency_fallbacks.md†L9-L17】 |
| MediaPipe | Provides face mesh landmarks for smoothing. | Overlays render without landmark feedback, reducing facial fidelity. | Restore MediaPipe on demo rigs or log the diminished tracking. 【F:docs/optional_dependency_fallbacks.md†L7-L14】 |
| ControlNet / AnimateDiff | Injects gesture animation into avatar output. | Gestural cues are omitted, leaving static upper-body motion. | Install ControlNet/AnimateDiff or choreograph manual gestures. 【F:docs/optional_dependency_fallbacks.md†L12-L17】 |
| vector_memory | Supplies scene-specific avatar traits. | Trait overrides are skipped and default skins persist. | Reconnect vector memory or annotate the missing personalization. 【F:docs/optional_dependency_fallbacks.md†L16-L17】 |
| lwm | Generates automated camera paths. | Camera automation is unavailable; scenes require manual paths. | Restore `lwm` or script alternate camera moves. 【F:docs/optional_dependency_fallbacks.md†L16-L17】 |
| sounddevice | Handles realtime playback and microphone capture. | Live audio I/O aborts, forcing silent or pre-rendered rehearsals. | Install `sounddevice` (with ALSA headers) or log silent-mode runs. 【F:docs/optional_dependency_fallbacks.md†L21-L24】 |
| opensmile | Extracts acoustic features for emotion telemetry. | Sentiment scores fall back to heuristics, reducing fidelity. | Install OpenSMILE or record the diminished metrics coverage. 【F:docs/optional_dependency_fallbacks.md†L23-L25】 |
| websockets | Streams listening telemetry to dashboards. | Streaming server errors prevent remote monitoring. | Re-enable the module or export logs offline. 【F:docs/optional_dependency_fallbacks.md†L25-L26】 |
| gTTS | Generates default spoken prompts. | Playback becomes a sine-wave placeholder with no intelligible speech. | Install gTTS or switch to another synthesis backend. 【F:docs/optional_dependency_fallbacks.md†L26-L27】 |
| OpenVoice | Performs advanced timbre morphing. | Falls back to coarse pitch-shift conversion only. | Restore OpenVoice or align expectations with simplified output. 【F:docs/optional_dependency_fallbacks.md†L27-L28】 |
| EmotiVoice | Provides neural voice cloning. | Cloned speech renders silent placeholders and low MOS scores. | Reinstall EmotiVoice or pre-record narration. 【F:docs/optional_dependency_fallbacks.md†L32-L33】 |
| librosa | Powers audio analysis, lip sync and DSP utilities. | Feature extraction and WAV persistence fail across the pipeline. | Provision the `librosa` extra or document analytics gaps. 【F:docs/optional_dependency_fallbacks.md†L10-L30】 |
| soundfile | Enables WAV export and DSP filters. | Audio assets cannot be saved or processed. | Install `soundfile` or capture alternate recordings. 【F:docs/optional_dependency_fallbacks.md†L29-L34】 |
| pydub / FFmpeg | Unlocks the full `AudioSegment` backend. | Resolver drops to NumPy with simplified DSP; playback errors without FFmpeg. | Restore FFmpeg and the `pydub` extra or highlight reduced mix controls. 【F:docs/optional_dependency_fallbacks.md†L30-L31】 |
| simpleaudio | Supports direct buffer playback. | Single-shot playback fails outside the pydub path. | Ship the audio extras bundle or rely on looped cues. 【F:docs/optional_dependency_fallbacks.md†L31-L32】 |
| RAVE / torch | Enables neural morphing and latent mixing. | RAVE helpers raise errors; morphing is unavailable. | Deploy the RAVE dependencies or log the disabled feature set. 【F:docs/optional_dependency_fallbacks.md†L33-L34】 |
| NSynth | Provides cross-timbral interpolation. | Interpolation raises errors and is skipped entirely. | Install NSynth tooling or capture the omission. 【F:docs/optional_dependency_fallbacks.md†L33-L34】 |

Stage leads should cross-reference the [Optional Dependency Fallback Matrix](optional_dependency_fallbacks.md)
when rehearsals run in degraded mode and attach the relevant excerpts to the
evidence bundle.

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
