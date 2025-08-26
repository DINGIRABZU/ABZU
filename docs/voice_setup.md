# Voice Model Setup

This guide explains how to install external text-to-speech models so ABZU can
produce spoken output.

## 1. Install a backend

Choose a TTS engine such as [Piper](https://github.com/rhasspy/piper) and
install it:

```bash
pip install piper-tts
```

## 2. Download a voice model

Create a directory for model weights and fetch a voice file. ABZU ships with a
helper to download a few common voices:

```bash
python download_models.py piper-en-amy-medium
```

The example below downloads an English voice for Piper and loads it once to
populate the cache. Any ONNX voice from the Piper repository can be substituted
for a different language or style:

```bash
mkdir -p voices
curl -L -o voices/en_US-amy-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-amy-medium.onnx
python - <<'PY'
from piper import PiperVoice
PiperVoice.load("voices/en_US-amy-medium.onnx")
PY
```

## 3. Configure voices

Copy or edit `voice_config.yaml` and `voice_avatar_config.yaml` to adjust
volume, pitch and tone for each archetype.

## 4. Set environment variables (optional)

Point `VOICE_CONFIG_PATH`, `VOICE_AVATAR_CONFIG_PATH` or `VOICE_TONE_PATH` to
custom locations if the files live outside the repository.

## 5. Verify synthesis

Start the CLI with `abzu start --speak` or launch the FastAPI server and
confirm speech is produced. For a quick command-line check you can run:

```bash
python -m src.cli.voice "Hello world"
```

Once cached, the engine will reuse the downloaded weights on subsequent runs.

