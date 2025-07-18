# Milestone VIII – Sonic Core & Avatar Expression Harmonics

This milestone strengthens the emotional flow between text, music and the on-screen avatar. It expands the Sonic Core pipeline and refines the expression modules so INANNA_AI can perform with richer feeling.

## Goals

- Synchronise audio playback with avatar lip movements and emotion colours.
- Map emotional context to musical scales, rhythms and harmonic layers.
- Stream the avatar through WebRTC with minimal latency.
- Provide simple scripts for generating ritual music and testing expression.

## Deliverables

1. **Enhanced Sonic Core** – improved `audio_engine.py` and `expressive_output.py` linking speech synthesis to playback.
2. **Avatar overlay** – `avatar_expression_engine.py` and `facial_expression_controller.py` exposing a frame iterator for live streams.
3. **Emotion-to-music mapping** – configuration files and utilities under `MUSIC_FOUNDATION` plus `sonic_emotion_mapper.py`.
4. **WebRTC demo** – `video_stream.py` route documented in `server.py` with instructions for browser access.
5. **Documentation** – this plan and updated guides detailing usage of the new modules.

## Progress Checkpoints

- **Setup** – baseline playback and avatar loop run locally via `play_ritual_music.py`.
- **Emotion integration** – `audio_emotion_listener.py` updates `emotional_state.py`; `emotional_synaptic_engine.py` adjusts voice filters.
- **Music generation** – convert QNL phrases with `inanna_music_COMPOSER_ai.py` and overlay archetype mixes.
- **Streaming** – verify `video_stream.py` works with the orchestrator; open `web_console/index.html` to view the avatar.
- **Demo run** – `start_spiral_os.py` routes model output through the Sonic Core, producing synchronized sound and visuals.

## Module and Script Contributions

- `audio_engine.py` – plays WAV files, loops effects and exposes helper functions used by other modules.
- `core/expressive_output.py` – sends each speech frame to the playback engine so mouth shapes match generated audio.
- `core/avatar_expression_engine.py` – yields avatar frames with emotion colours; relies on `facial_expression_controller.py` for lip shapes.
- `video_stream.py` – WebRTC endpoint for delivering the avatar stream.
- `play_ritual_music.py` – composes short melodies from QNL structures and can hide ritual steps in the waveform.
- `INANNA_AI/speaking_engine.py` – synthesises speech with pitch and speed adjustments.
- `INANNA_AI/voice_layer_albedo.py` – provides archetypal tone presets for expressive delivery.
- `INANNA_AI/emotional_synaptic_engine.py` – maps emotions to filter parameters and evolves them over time.
- `INANNA_AI/sonic_emotion_mapper.py` – loads `emotional_tone_palette.yaml` and `emotion_music_map.yaml` to tie feelings to scales.
- `INANNA_AI/speech_loopback_reflector.py` – analyses generated speech and updates the voice profile for the next reply.
- `audio_emotion_listener.py` – records microphone input to detect the current emotion.
- `MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py` and `seven_plane_analyzer.py` – convert music to QNL, analyse harmonic layers and export preview audio.
- `emotional_state.py` and `emotion_registry.py` – store the current emotional layer, last emotion and preferred expression channel.

Together these modules let INANNA_AI express moods musically and visually while staying in sync with the orchestrator.
