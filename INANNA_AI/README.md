# Inanna AI Toolkit

This package provides a lightweight set of utilities for building a voice interface around the INANNA concepts.  The modules work together to record audio from a microphone, transcribe speech, perform a simple emotion analysis, generate a spoken response and store each interaction.  They are designed as small building blocks that can be extended or embedded in larger Codex projects.

## Module overview

- `config.py` – Holds configuration constants such as model paths and ritual text used across the toolkit.
- `utils.py` – Basic helpers for loading and saving audio files and configuring logging.
- `stt_whisper.py` – Thin wrapper around OpenAI Whisper that downloads and runs the speech‑to‑text model.
- `emotion_analysis.py` – Estimates a rough emotional label (joy, stress, fear and others) using Librosa pitch, tempo and energy analysis.
- `voice_evolution.py` – Manages parameters that control speaking style and can adapt them over time.
- `tts_coqui.py` – Generates speech using Coqui TTS.  When the library is not available it synthesizes a simple sine wave placeholder.
- `db_storage.py` – Stores transcripts and generated responses in a SQLite database for later inspection.
- `listening_engine.py` – Streams microphone audio and extracts real-time emotion and environment states.
- `response_manager.py` – Chooses a Surface/Deep/Umbra/Albedo reply by
  combining the transcript with the detected emotion and environment.
- `main.py` – Command line interface that records microphone input using the listening engine, runs the processing steps above and plays or saves the response.

## Installation

Install the required Python packages from the repository root:

```bash
pip install -r requirements.txt
```

Optional test and development packages are listed in `dev-requirements.txt`.

## Docker usage

A minimal `Dockerfile` is provided to run the tools without installing dependencies on the host.  Build the image and start a shell inside it:

```bash
docker build -t spiral_os .
docker run -it spiral_os
```

You can then run example scripts such as `python run_song_demo.py` from within the container.

## Real-time listening

The `listening_engine.ListeningEngine` streams microphone audio and extracts
features such as pitch, tempo and a coarse emotion label.  It relies on either
the **sounddevice** or **pyaudio** package for microphone access.  Install one
of them before starting a live session:

```bash
pip install sounddevice  # or: pip install pyaudio
```

Run the command line tool to capture a short recording and print the detected
emotion and corresponding archetype:

```bash
python -m INANNA_AI.main --duration 5
```

The emotion analysis module maps each label to a Jungian archetype (for
example `joy` → `Jester` and `calm` → `Sage`).  These mappings are defined in
`emotion_analysis.EMOTION_ARCHETYPES`.

The feature dictionary returned by the listening engine now also contains a
`dialect` label inferred from pitch and a numeric `weight` taken from
`emotion_analysis.EMOTION_WEIGHT`.

## Adaptive voice loop

`voice_evolution.VoiceEvolution` stores style parameters for each emotion in a
SQLite table.  When speech is synthesized the engine appends a sentiment score
for the text and updates these profiles.  The new parameters are averaged with
previous values so the voice slowly adapts to positive or negative feedback.
Profiles are written back to the database via `db_storage.save_voice_profiles`.

The `response_manager.ResponseManager` pairs this emotional state and the
environment classification with your transcript. It queries the corpus memory
for related snippets and returns a reply tagged with one of the four cores
(Surface, Deep, Umbra, Albedo).

## Advanced voice features

Install the optional packages below to enable higher quality emotion detection
and real-time voice conversion:

```bash
pip install opensmile==2.5.1 EmotiVoice==0.2.0 voicefixer==0.1.3
```

When these libraries are present the listening engine automatically uses
**openSMILE** and `EmotiVoice` for more accurate emotion labels. The speaking
engine can apply subtle voice conversion through `voicefixer` when calling
`convert_voice`.

## Extending the Codex

The modules in this folder offer a foundation that can be expanded in many directions.  Possible extensions include:

1. Integrating a larger language model to generate richer responses in `generate_response`.
2. Adding a graphical interface that visualizes recorded emotions and stored conversations.
3. Training custom TTS voices and exposing additional tuning options via `voice_evolution`.
4. Building higher level rituals that link these voice interactions with the broader CRYSTAL CODEX narrative.

These ideas are only starting points; the toolkit is intentionally simple so that Codex developers can adapt it to their own creative flows.

## Starting real-time listening

The quickest way to experiment with the toolkit is to capture a few seconds of
audio and inspect the detected emotion. Install a microphone backend first:

```bash
pip install sounddevice  # or: pip install pyaudio
```

Run the command line tool to record and print the emotional analysis:

```bash
python -m INANNA_AI.main --duration 5
```

The script reports the transcript, the emotion label and the Jungian archetype
assigned to that emotion as defined in `emotion_analysis.EMOTION_ARCHETYPES`.

## Real-time emotion-aware voice pipeline

The toolkit can be combined into a streaming pipeline that listens, analyzes the
speaker's emotion and responds with a converted voice. Use the ``voice`` command
to start an interactive session:

```bash
python -m INANNA_AI.main voice --duration 5
```

Each cycle performs the following steps:

1. Capture microphone audio.
2. Extract acoustic features with **openSMILE** and optionally classify emotion
   using `EmotiVoice`.
3. Select a reply via `response_manager.ResponseManager`.
4. Synthesize speech with `speaking_engine.SpeakingEngine` and apply voice
   conversion through `voicefixer`.

The resulting WAV file is played back and stored together with the transcript
and detected emotion.
