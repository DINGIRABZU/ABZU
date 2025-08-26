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

Create a directory for model weights and fetch a voice file. The example below
downloads an English voice for Piper and loads it once to populate the cache:

```bash
mkdir -p voices
curl -L -o voices/en_US-amy-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-amy-medium.onnx
python - <<'PY'
from piper import PiperVoice
PiperVoice.load("voices/en_US-amy-medium.onnx")
PY
```

## 3. Configure ABZU

Copy or edit `voice_config.yaml` and `voice_avatar_config.yaml` to adjust
volume, pitch and tone. Environment variables such as `VOICE_CONFIG_PATH` and
`VOICE_AVATAR_CONFIG_PATH` can point to custom locations.

## 4. Verify synthesis

Start the CLI with `abzu start --speak` or launch the FastAPI server and
confirm speech is produced. Once cached, the engine will reuse the downloaded
weights on subsequent runs.

