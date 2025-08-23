# Full Setup

The full installation enables all Spiral OS features.

## Python installation

Install with every extras group:

```bash
pip install -e .[llm,audio,ml,vision,web,network,extras]
```

## Extras overview

- `audio` – audio processing (`librosa`, `ffmpeg-python`, etc.)
- `llm` – large language model stacks (`torch`, `transformers`)
- `ml` – analytics and vector stores (`pandas`, `chromadb`, `mlflow`)
- `vision` – computer vision and automation (`opencv`, `aiortc`, `selenium`)
- `web` – APIs and streaming (`fastapi`, `uvicorn`, `streamlit`)
- `network` – packet capture and analysis (`scapy`)
- `extras` – experimental or heavyweight models (`stable-baselines3`, `wav2lip`)
- `dev` – development helpers for tests and formatting

## Required system packages

The project expects these commands in the environment:

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
