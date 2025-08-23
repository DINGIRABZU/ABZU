# Minimal Setup

The minimal installation provides only the core Spiral OS utilities.

## Python installation

Install the package without extras:

```bash
pip install -e .
# or
pip install -e .[minimal]
```

## Optional extras

Install extras to enable additional domains:

- `audio` – audio processing (`librosa`, `ffmpeg-python`, etc.)
- `llm` – large language model stacks (`torch`, `transformers`)
- `ml` – analytics and vector stores (`pandas`, `chromadb`, `mlflow`)
- `vision` – computer vision and automation (`opencv`, `aiortc`, `selenium`)
- `web` – APIs and streaming (`fastapi`, `uvicorn`, `streamlit`)
- `network` – packet capture and analysis (`scapy`)
- `extras` – experimental or heavyweight models (`stable-baselines3`, `wav2lip`)
- `dev` – development helpers for tests and formatting

Install only the groups you need, for example:

```bash
pip install -e .[llm,audio]
```

## Required system packages

Ensure these commands are available before running the project:

- docker
- nc
- sox
- ffmpeg
- curl
- jq
- wget
- aria2c

### Debian/Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y docker.io netcat-openbsd sox ffmpeg curl jq wget aria2
```

### macOS

```bash
brew install docker netcat sox ffmpeg curl jq wget aria2
```
