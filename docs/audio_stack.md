# Audio Stack Dependencies

The Stage B rehearsal pipeline relies on the `audio` extras group plus a
small set of optional analyzers. The table below summarises each dependency,
its role and the behaviour when it is not available.

| Component | Provided by | Role | Behaviour when missing |
| --- | --- | --- | --- |
| Core playback | `pydub` | Primary backend used by `audio.segment` and `audio.engine` for decoding and transformations. | The loader drops to the NumPy segment implementation when pydub or FFmpeg are unavailable, logging an error and offering only basic overlay/panning features.【F:src/audio/segment.py†L4-L104】 |
| Realtime output | `simpleaudio` | Non-blocking playback invoked by the audio engine and CLI tools. | `audio.backends` falls back to a no-op backend that only writes WAV files when neither `soundfile` nor `simpleaudio` are present.【F:src/audio/backends.py†L1-L69】 |
| File I/O + MOS | `soundfile` | Persists generated tones and powers NumPy fallback segments as well as MOS estimation. | Loading/saving raises a `RuntimeError` without `soundfile`; the voice cloner degrades to a baseline MOS of 1.0 when it cannot read waveforms.【F:src/audio/segment.py†L60-L120】【F:src/audio/voice_cloner.py†L70-L116】 |
| Feature extraction | `librosa` | Loads audio and computes MFCC/chroma/tempo descriptors. | `audio.audio_ingestion` raises a `RuntimeError` for loaders and feature helpers until librosa is installed.【F:src/audio/audio_ingestion.py†L12-L81】 |
| Emotion features | `opensmile` | Supplies additional descriptors for emotion-aware rehearsal metrics. | The environment check logs a warning when `opensmile` is missing so Stage B runs can note reduced telemetry coverage.【F:src/audio/check_env.py†L12-L44】 |
| DSP filters | `ffmpeg` binary | Required for pydub decoding, DSP filters and loop playback. | The engine aborts playback when FFmpeg is missing and the loader switches to the NumPy backend to avoid crashes.【F:src/audio/segment.py†L60-L83】【F:src/audio/engine.py†L183-L207】 |
| Capture | `sounddevice` | Records rehearsal voice samples for cloning. | The recorder emits silence and logs a warning when `sounddevice` is absent so the workflow still completes.【F:src/audio/voice_cloner.py†L32-L60】 |
| Voice synthesis | `EmotiVoice` | Generates cloned speech from captured samples. | The synthesiser emits silence of appropriate duration and logs a warning when EmotiVoice is not installed.【F:src/audio/voice_cloner.py†L62-L93】 |
| Spectral extras | `essentia` | Enhances key/tempo detection beyond librosa estimators. | When Essentia is missing the helpers fall back to librosa algorithms automatically.【F:src/audio/audio_ingestion.py†L29-L59】 |
| Latent morphing | `rave`, `torch` | Enables RAVE encode/decode and morph operations for ritual audio. | RAVE helpers raise `RuntimeError` and voice aura skips morphing when the library or torch backend is unavailable.【F:src/audio/dsp_engine.py†L95-L153】【F:src/audio/voice_aura.py†L92-L99】 |
| CLAP embeddings | `transformers` (CLAP) | Produces audio/text embeddings for retrieval. | `embed_clap` raises a `RuntimeError` until the CLAP processor, model and torch are installed.【F:src/audio/audio_ingestion.py†L33-L177】 |

## Stage B audio extras inventory

| Dependency | Version | Provisioned via | Primary usage |
| --- | --- | --- | --- |
| Librosa | 0.11.0 | `requirements.txt` / `scripts/setup_audio_env.sh` | Feature extraction for ingestion and rehearsal analytics (`audio_ingestion`, MUSIC foundation utilities).【F:requirements.txt†L24-L28】【F:scripts/setup_audio_env.sh†L1-L62】【F:MUSIC_FOUNDATION/music_foundation.py†L18-L67】 |
| PyDub + FFmpeg | 0.25.1 / system FFmpeg | `requirements.txt` / `scripts/setup_audio_env.sh`; `audio.check_env` enforces binary presence. Script now auto-installs FFmpeg when package managers are available. | Primary playback backend for segment/engine; FFmpeg enables decoding, looping and DSP paths.【F:requirements.txt†L20-L36】【F:scripts/setup_audio_env.sh†L1-L62】【F:src/audio/segment.py†L45-L120】【F:src/audio/engine.py†L37-L207】【F:src/audio/check_env.py†L9-L61】 |
| Simpleaudio | 1.0.4 | `scripts/setup_audio_env.sh` | Non-blocking playback backend; avoids rehearsal fallbacks to file-only renders.【F:scripts/setup_audio_env.sh†L48-L57】【F:src/audio/backends.py†L1-L69】 |
| OpenSMILE | 2.6.0 | `requirements.txt` / `scripts/setup_audio_env.sh` | Emotion descriptors for listening and rehearsal telemetry.【F:requirements.txt†L29-L36】【F:scripts/setup_audio_env.sh†L48-L57】【F:INANNA_AI/listening_engine.py†L21-L145】 |
| EmotiVoice | 0.2.0 | `scripts/setup_audio_env.sh` / `pyproject.toml` extra | Voice cloning output for avatar narration when the optional synthesiser is available.【F:scripts/setup_audio_env.sh†L48-L57】【F:pyproject.toml†L74-L83】【F:src/audio/voice_cloner.py†L62-L116】 |
| CLAP shim | 0.7.1.post1 | `vendor/clap_stub` via `scripts/setup_audio_env.sh` | Provides the CLAP processor/model import so retrieval telemetry loads the LAION checkpoints without legacy package errors.【F:scripts/setup_audio_env.sh†L59-L62】【F:vendor/clap_stub/clap/__init__.py†L1-L21】【F:src/audio/audio_ingestion.py†L163-L205】 |
| RAVE shim | 0.1.0 | `vendor/rave_stub` via `scripts/setup_audio_env.sh` | Supplies minimal encode/decode hooks for DSP morphing when full RAVE builds are unavailable.【F:scripts/setup_audio_env.sh†L59-L62】【F:vendor/rave_stub/rave/__init__.py†L1-L40】【F:src/audio/dsp_engine.py†L95-L142】 |

Operators should validate this matrix during rehearsals and capture any
intentional degradations in the run log alongside the `audio.check_env`
transcript.

## Automated rehearsal host provisioning

Stage B rehearsal hosts install and verify this bundle automatically.
The `stage-b-rehearsal` pipeline now invokes `scripts/setup_audio_env.sh`
before running smoke checks so every run refreshes the pinned Python
packages, installs FFmpeg when a package manager is available, layers the
local CLAP/RAVE shims, and executes the strict environment
validation.【F:deployment/pipelines/stage_b_rehearsal.yml†L1-L47】【F:scripts/setup_audio_env.sh†L1-L62】
Operators preparing a new host should run the same script manually to
mirror the pipeline behaviour and capture its validation transcript in
the rehearsal evidence bundle.
