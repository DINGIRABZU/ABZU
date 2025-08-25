# Voice Cloner

The `VoiceCloner` utility records a short sample of a speaker and synthesises
new speech in the captured voice. It exposes both a command line interface and
REST endpoints.

## CLI usage

Record a sample and synthesise a phrase:

```bash
python -m src.cli.voice_clone capture sample.wav --speaker alice
python -m src.cli.voice_clone synthesize "Hello" out.wav --sample sample.wav --speaker alice
```

The synthesis command logs a crude Mean Opinion Score (MOS) estimate indicating
quality on a scale from 1 to 5. When optional dependencies are missing, silent
audio is generated and the MOS defaults to 1.

## REST API

The FastAPI server exposes matching endpoints:

- `POST /voice/capture` – store a voice sample.
- `POST /voice/synthesize` – generate speech and return the MOS metric.

These endpoints accept JSON bodies containing `speaker`, `text` and file paths.
When audio backends are unavailable the server falls back to silent audio
production and reports a low MOS score.
