# Module Index

## `src/__init__.py`
Top-level package exposing core submodules.

## `src/api/__init__.py`
Package initialization.

## `src/api/server.py`
FastAPI server providing video generation and avatar streaming APIs.

## `src/audio/__init__.py`
Audio processing utilities and playback helpers.

## `src/audio/audio_ingestion.py`
Audio ingestion module for audio.

### Functions
- **load_audio** – Load audio using :func:`librosa.load`.
- **extract_mfcc** – Return MFCC features for ``samples``.
- **extract_key** – Return detected musical key using Essentia if available.
- **extract_tempo** – Return tempo estimated by Essentia when present or Librosa fallback.
- **extract_chroma** – Return chroma representation of ``samples``.
- **extract_spectral_centroid** – Return spectral centroid of ``samples``.
- **extract_chords** – Estimate chord sequence using simple template matching.
- **separate_sources** – Separate ``samples`` using Spleeter or Demucs.
- **extract_features** – Load ``path`` and return a dictionary of audio descriptors.
- **embed_clap** – Return CLAP embedding of ``samples`` if the model is installed.

## `src/audio/backends.py`
Audio playback backends.

### Classes
- **SoundfileBackend** – Backend that uses ``soundfile`` for writing and playback.
- **SimpleAudioBackend** – Backend that plays audio via ``simpleaudio``.
- **NoOpBackend** – Backend used when no audio library is available.

### Functions
- **get_backend** – Return an appropriate playback backend.

## `src/audio/check_env.py`
Diagnostic CLI to verify audio dependencies are installed.

### Functions
- **check_packages** – Attempt to import each required package and return status information.
- **main** – Print the installation status of required audio packages.

## `src/audio/dsp_engine.py`
Basic audio DSP utilities primarily using ffmpeg.

### Functions
- **pitch_shift** – Shift ``data`` by ``semitones`` using ``ffmpeg``.
- **time_stretch** – Change playback speed of ``data`` without altering pitch.
- **compress** – Apply dynamic range compression using ``ffmpeg``.
- **rave_encode** – Return RAVE latents for ``data`` using ``checkpoint``.
- **rave_decode** – Synthesize audio from RAVE ``latents``.
- **rave_morph** – Interpolate between ``data_a`` and ``data_b`` via RAVE latents.
- **nsynth_interpolate** – Interpolate ``data_a`` and ``data_b`` using NSynth.

## `src/audio/emotion_params.py`
Emotion to music parameter resolution helpers.

### Functions
- **resolve** – Return tempo, melody, wave type and resolved archetype.

## `src/audio/engine.py`
Simple playback engine for ritual loops and voice audio.

### Functions
- **get_asset_path** – Return path to ``name`` or synthesize a temporary tone if missing.
- **play_sound** – Play an audio file optionally in a loop.
- **stop_all** – Stop all currently playing sounds and loops.

## `src/audio/mix_tracks.py`
Utility script for mixing audio files.

### Functions
- **mix_audio** – Return mixed audio and transition info.
- **mix_from_instructions** – Return mixed audio according to ``instr`` JSON structure.
- **main** – 

## `src/audio/play_ritual_music.py`
Compose short ritual music based on emotion and play it.

### Classes
- **RitualTrack** – Dataclass representing a generated ritual track.

### Functions
- **map_emotion** – Resolve music parameters for ``emotion`` and ``archetype`` with caching.
- **synthesize_waveform** – Generate a waveform for the given ``melody``.
- **encode_stego** – Optionally embed a secret phrase into ``wave``.
- **playback** – Play ``wave`` using the best available backend.
- **compose_ritual_music** – Generate a simple melody and optionally hide ritual steps.
- **main** – 

## `src/audio/segment.py`
Minimal audio segment abstraction with optional NumPy backend.

### Classes
- **NpAudioSegment** – Lightweight replacement for :class:`pydub.AudioSegment`.

### Functions
- **has_ffmpeg** – Return ``True`` if the ``ffmpeg`` binary is available and executable.

## `src/audio/stego.py`
Steganography helpers for ritual music.

### Functions
- **load_ritual_profile** – Return ritual mappings loaded from ``path`` if available.
- **embed_phrase** – Embed ritual phrase for ``emotion`` into ``wave`` if configured.

## `src/audio/voice_aura.py`
Apply reverb and timbre effects based on the current emotion.

### Functions
- **sox_available** – Return ``True`` when the ``sox`` binary is available.
- **apply_voice_aura** – Return a processed copy of ``path`` with emotion-derived effects.

## `src/audio/voice_cloner.py`
Clone a user's voice using the optional EmotiVoice library.

### Classes
- **VoiceCloner** – Capture a short sample and synthesise cloned speech.

## `src/audio/waveform.py`
Waveform synthesis utilities.

### Functions
- **synthesize** – Return a waveform for ``melody`` at ``tempo`` using ``wave_type``.

## `src/cli.py`
Unified command line interface for Spiral OS tools.

### Functions
- **build_parser** – 
- **main** – Entry point for the command line script.

## `src/cli/__init__.py`
Command-line interface utilities.

### Functions
- **main** – Entry point for the consolidated ``abzu`` CLI.

## `src/cli/console_interface.py`
Interactive REPL for the Crown agent.

### Functions
- **run_repl** – Start the interactive console.

## `src/cli/music_helper.py`
Utility functions for handling music generation commands.

### Functions
- **play_music** – Generate and play music for ``prompt`` using ``orch``.

## `src/cli/sandbox_helper.py`
Run code patches in an isolated sandbox and execute tests.

### Functions
- **run_sandbox** – Apply a patch file in a sandbox and run tests.

## `src/cli/spiral_cortex_terminal.py`
Command line tool for exploring ``cortex_memory_spiral.jsonl``.

### Functions
- **run_query** – Print entries matching ``filters``.
- **run_dreamwalk** – Display entries one by one with short delays.
- **run_stats** – Show emotion and event statistics and archetype suggestion.
- **main** – 

## `src/cli/voice.py`
Command line tool to synthesize speech and play or stream it.

### Functions
- **play_frame** – Render ``frame`` to the local display if OpenCV is available.
- **send_frame** – Forward ``frame`` to an animation subsystem via HTTP.
- **main** – Entry point for the voice synthesizer.

## `src/cli/voice_clone.py`
CLI for recording samples and synthesizing speech via :mod:`EmotiVoice`.

### Functions
- **main** – Entry point for the voice cloning utility.

## `src/cli/voice_clone_helper.py`
Helper for voice cloning within the console interface.

### Functions
- **clone_voice** – Capture a voice sample and synthesize ``sample_text``.

## `src/core/__init__.py`
Core package exposing primary services.

## `src/core/avatar_expression_engine.py`
Synchronise avatar expressions with audio playback.

### Functions
- **stream_avatar_audio** – Yield avatar frames while playing ``audio_path``.

## `src/core/code_introspector.py`
Utilities for inspecting repository code.

### Functions
- **iter_modules** – Yield Python modules under *root*.
- **get_snippet** – Return the first ``lines`` lines from ``path``.
- **analyze_repository** – Write a simple code analysis log and return collected snippets.

## `src/core/config.py`
Validated configuration loading using Pydantic.

### Classes
- **ServicesConfig** – Endpoints for external services used by the application.
- **AudioConfig** – Audio processing parameters.
- **Config** – Top level configuration validated by Pydantic.

### Functions
- **load_config** – Load and validate ``name`` from the :mod:`config` directory.

## `src/core/context_tracker.py`
Simple runtime context flags.

### Classes
- **ContextTracker** – State flags describing the current multimodal session.

## `src/core/contracts.py`
Protocol definitions for cross-module services.

### Classes
- **EmotionAnalyzerService** – Analyze emotional content and maintain mood state.
- **MemoryLoggerService** – Persist interaction history and ritual results.

## `src/core/emotion_analyzer.py`
Mood tracking and emotion analysis utilities.

### Classes
- **EmotionAnalyzer** – Track recent emotions and expose analysis helpers.

## `src/core/expressive_output.py`
Coordinate speech synthesis, playback and avatar frames.

### Functions
- **set_frame_callback** – Register ``func`` to receive avatar frames.
- **set_background** – Set ``path`` as looping background music.
- **speak** – Synthesize speech and trigger playback.
- **play_audio** – Play ``path`` via the audio engine.
- **make_gif** – Return GIF bytes showing the avatar mouthing ``audio_path``.

## `src/core/facial_expression_controller.py`
Basic facial expression control utilities.

### Functions
- **get_current_expression** – Return the expression colour for the last recorded emotion.
- **apply_expression** – Return ``frame`` modified according to ``emotion``.

## `src/core/feedback_logging.py`
Manage feedback logs and thresholds with on-disk persistence.

### Functions
- **load_feedback** – Return all feedback entries from :data:`LOG_FILE`.
- **append_feedback** – Append ``entry`` to :data:`LOG_FILE` with a timestamp.

## `src/core/language_engine.py`
Speech synthesis wrapper that optionally routes audio via a connector.

### Functions
- **register_audio_callback** – Set ``func`` to be called with the synthesized audio path.
- **register_connector** – Store ``connector`` used for call routing.
- **synthesize_speech** – Generate speech and route it via the active callback.

## `src/core/memory_logger.py`
Wrapper around corpus memory logging helpers.

### Classes
- **MemoryLogger** – Provide methods for storing interaction history.

## `src/core/memory_physical.py`
Storage utilities for raw physical inputs.

### Classes
- **PhysicalEvent** – Container for raw physical inputs.

### Functions
- **store_physical_event** – Persist a physical event and accompanying metadata.

## `src/core/model_selector.py`
Model selection and benchmarking utilities.

### Classes
- **ModelSelector** – Pick the best language model and update routing weights.

## `src/core/self_correction_engine.py`
Self-correct emotional output using recent feedback.

### Functions
- **adjust** – Adjust avatar tone when ``detected`` diverges from ``intended``.

## `src/core/task_parser.py`
Simple text command parser returning structured intents.

### Functions
- **parse** – Return intents detected in ``text``.

## `src/core/task_profiler.py`
Task profiling helpers.

### Classes
- **TaskProfiler** – Classify text inputs and map ritual action sequences.

## `src/core/utils/optional_deps.py`
Helpers for optional dependencies with lightweight stubs.

### Functions
- **lazy_import** – Return ``name`` if import succeeds, otherwise a lightweight stub.

## `src/core/utils/seed.py`
Utilities for deterministic behaviour.

### Functions
- **seed_all** – Seed Python, NumPy and PyTorch random number generators.

## `src/core/video_engine.py`
Avatar video generation utilities.

### Classes
- **AvatarTraits** – Simple avatar trait configuration.

### Functions
- **register_face_pipeline** – Register a face processing pipeline.
- **register_gesture_pipeline** – Register a gesture processing pipeline.
- **generate_avatar_stream** – Yield RGB frames representing the configured avatar.
- **start_stream** – Return an iterator producing avatar frames.

## `src/dashboard/__init__.py`
Dashboard components for monitoring and mixing.

## `src/dashboard/app.py`
Streamlit dashboard for visualising LLM performance.

## `src/dashboard/qnl_mixer.py`
Tools for mixing QNL audio inside Streamlit.

## `src/dashboard/rl_metrics.py`
Streamlit dashboard for reinforcement learning metrics.

## `src/dashboard/system_monitor.py`
System resource monitoring utilities.

### Functions
- **collect_stats** – Gather basic CPU, memory and network usage statistics.
- **main** – Run the system monitor command line interface.

## `src/dashboard/usage.py`
Streamlit dashboard for usage metrics.

## `src/health/__init__.py`
Health check utilities for Spiral OS.

## `src/health/boot_diagnostics.py`
Boot diagnostics for verifying essential services.

### Functions
- **run_boot_checks** – Import each vital module and report availability.

## `src/health/essential_services.py`
List of core modules required for Spiral OS boot diagnostics.

## `src/init_crown_agent.py`
Load Crown agent configuration and expose model endpoints.

### Functions
- **load_crown_config** – Return configuration dictionary merged with ``os.environ`` overrides.
- **get_model_endpoints** – Return a mapping of active model names to their URLs.

## `src/lwm/__init__.py`
Large World Model package.

## `src/lwm/config_model.py`
Configuration model for the Large World Model.

### Classes
- **GPUConfig** – GPU flags controlling CUDA usage.
- **PathConfig** – Filesystem paths used by the Large World Model.
- **LWMConfig** – Aggregate configuration for the Large World Model.

### Functions
- **load_config** – Load an ``LWMConfig`` from ``config_path``.

## `src/lwm/large_world_model.py`
Minimal Large World Model converting 2D frames into a 3D scene.

### Classes
- **LargeWorldModel** – Construct simple 3D scenes from 2D image frames.

## `src/media/__init__.py`
Unified media interfaces for audio, video, and avatar.

## `src/media/audio/__init__.py`
Audio generation and playback interface.

## `src/media/audio/backends.py`
Utilities for loading optional audio backends.

### Functions
- **load_backend** – Return imported module ``name`` or ``None`` if unavailable.

## `src/media/audio/base.py`
Audio-specific media processing interfaces.

### Classes
- **AudioProcessor** – Base class for audio processors.

## `src/media/audio/generation.py`
Audio generation utilities with optional dependencies.

### Functions
- **generate_waveform** – Generate a sine wave audio segment.

## `src/media/audio/playback.py`
Audio playback utilities with optional dependencies.

### Functions
- **play_waveform** – Play an audio file using ``ffmpeg``.

## `src/media/avatar/__init__.py`
Avatar generation and playback interface.

## `src/media/avatar/base.py`
Avatar-specific media processing interfaces.

### Classes
- **AvatarProcessor** – Base class for avatar processors.

## `src/media/avatar/generation.py`
Avatar generation utilities composed from audio and video.

### Functions
- **generate_avatar** – Generate avatar media.

## `src/media/avatar/playback.py`
Avatar playback utilities.

### Functions
- **play_avatar** – Play avatar audio and video streams together.

## `src/media/base.py`
Common media processing interfaces.

### Classes
- **MediaProcessor** – Abstract base class for media processors.

## `src/media/video/__init__.py`
Video generation and playback interface.

## `src/media/video/base.py`
Video-specific media processing interfaces.

### Classes
- **VideoProcessor** – Base class for video processors.

## `src/media/video/generation.py`
Video generation utilities with optional dependencies.

### Functions
- **generate_video** – Create a video from image frames with optional 3D scene generation.

## `src/media/video/playback.py`
Video playback utilities with optional dependencies.

### Functions
- **play_video** – Play a video file using ``ffmpeg``.

## `src/spiral_os/__init__.py`
Spiral OS package providing command-line tools.

## `src/spiral_os/__main__.py`
Command-line interface for Spiral OS utilities.

### Functions
- **deploy_pipeline** – Execute each step listed in a pipeline YAML file.
- **start_os** – Launch the ``start_spiral_os`` sequence with forwarded arguments.
- **main** – Entry point for the ``spiral-os`` command line interface.

## `src/spiral_os/_hf_stub.py`
Minimal stub of the `huggingface_hub` package used in tests.

### Classes
- **HfHubHTTPError** – Placeholder exception matching the real library's error type.

### Functions
- **snapshot_download** – Return an empty string without performing any download.

## `src/spiral_os/start_spiral_os.py`
Launch the Spiral OS initialization sequence.

### Functions
- **main** –
