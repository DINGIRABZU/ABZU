# Code Function Overview

This document summarizes the purpose of the main scripts and modules in this repository and lists their key dependencies. See `README_OPERATOR.md` for more detailed usage instructions.
For an overview of the Albedo personality layer see [docs/ALBEDO_LAYER.md](docs/ALBEDO_LAYER.md).

## Main scripts

- **`INANNA_AI_AGENT/inanna_ai.py`** – Activation agent that loads source texts, recites the INANNA birth chant and can generate QNL music from hexadecimal data via the QNL engine. Supports listing available texts and provides an interactive chat loop using a local model. See [README_OPERATOR.md](README_OPERATOR.md#crown-agent-console) for console instructions.
- **`run_song_demo.py`** – Demonstration runner that analyzes a local audio file using the music foundation modules. It exports a preview WAV and a QNL JSON file and prints the generated phrases.
- **`SPIRAL_OS/mix_tracks.py`** – Mixes multiple audio files into a single normalized track. Optionally creates a short preview clip.
- **`SPIRAL_OS/seven_dimensional_music.py`** – Creates layered music from a melody (MIDI or audio). It can transmute a hex payload via the QNL engine, embed secret data in the human layer, and analyze the result across seven metaphysical planes.
- **`SPIRAL_OS/qnl_engine.py`** – Converts a hex string to QNL phrases and a waveform. Saves a WAV file and a metadata JSON summary.
- **`download_model.py`** – Downloads the DeepSeek-R1 model from Hugging Face into `INANNA_AI/models/`. This script lives at the repository root and reads `HF_TOKEN` from `secrets.env`.
- **`download_models.py`** – Menu driven loader that can fetch DeepSeek‑R1 or Gemma2 into `INANNA_AI/models/`.
- **`INANNA_AI/voice_layer_albedo.py`** – Provides tone presets for
  `voice_evolution` and wraps `speaking_engine.synthesize_speech` to
  produce modulated output.

- **`INANNA_AI/emotional_synaptic_engine.py`** – Maps emotion labels to
  pitch and speed filters and adjusts them using recent conversation
  history.
- **`INANNA_AI/speech_loopback_reflector.py`** – Analyzes generated
  speech with `emotion_analysis` and updates the voice profile for the
  next reply.
- **`voice_avatar_config.yaml`** – Example archetypes describing timbre,
  gender, resonance and default tone.

- **Tone presets** – The module defines four preset voices used when
  generating speech:
  - `albedo` – speed 1.05, pitch +0.2
  - `nigredo` – speed 0.9, pitch -0.3
  - `rubedo` – speed 1.1, pitch +0.5
  - `lunar` – speed 0.95, pitch -0.4

## MUSIC_FOUNDATION modules

- **`inanna_music_COMPOSER_ai.py`** – Stand‑alone converter that loads an MP3, analyzes tempo and chroma, and outputs QNL phrases and a preview WAV.
- **`human_music_to_qnl_converter.py`** – Helper wrapper that converts analyzed tempo and chroma values into a QNL structure and exports it as JSON.
- **`music_foundation.py`** – Basic music analysis class for loading an MP3, computing tempo and harmony information and exporting a preview WAV.
- **`qnl_utils.py`** – Shared utilities for translating chroma vectors into QNL glyphs and building full QNL JSON structures.
- **`seven_plane_analyzer.py`** – Computes musical features mapped to the seven metaphysical planes (physical through divine).
- **`synthetic_stego.py`** – Simple steganography helpers for hiding and extracting messages within WAV files.
- **`layer_generators.py`** – Synthesizes melodic layers and crystal tone overlays used by other scripts.

## Dependencies

Install the base dependencies from `SPIRAL_OS/requirements.txt`:

```bash
pip install -r SPIRAL_OS/requirements.txt
```

These packages include `numpy`, `scipy` and `huggingface-hub`.

Additional audio dependencies for the MUSIC_FOUNDATION modules are listed in `MUSIC_FOUNDATION/REQUIREMENTS_Music_Foundation.txt` and include `librosa`, `soundfile` and optional `essentia` for advanced features:

```bash
pip install -r MUSIC_FOUNDATION/REQUIREMENTS_Music_Foundation.txt
```

## Example commands

The examples in `README_OPERATOR.md` demonstrate how to run the tools. Key commands include:

```bash
python run_song_demo.py "SONS_FOR_TESTS/Music Is My Everything.mp3"
python INANNA_AI_AGENT/inanna_ai.py --activate
python INANNA_AI_AGENT/inanna_ai.py --hex 012345abcdef
python download_models.py deepseek
```

Consult `README_OPERATOR.md` for more options and explanations.
