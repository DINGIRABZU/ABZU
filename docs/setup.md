# Environment Setup

This guide lists the system packages and environment variables required to run the project.

## Installation

### Minimal installation

Install only the core Spiral OS utilities:

```bash
pip install -e .[minimal]
```

### Optional dependency groups

Each extra installs heavier libraries for a specific domain:

- `audio` – audio processing (`librosa`, `ffmpeg-python`, etc.)
- `llm` – large language model stacks (`torch`, `transformers`)
- `ml` – analytics and vector stores (`pandas`, `chromadb`, `mlflow`)
- `vision` – computer vision and automation (`opencv`, `aiortc`, `selenium`)
- `web` – APIs and streaming (`fastapi`, `uvicorn`, `streamlit`)
- `network` – packet capture and analysis (`scapy`)
- `extras` – experimental or heavyweight models (`stable-baselines3`, `wav2lip`)
- `dev` – development helpers for tests and formatting

Install the groups you need, for example:

```bash
pip install -e .[llm,audio]
```

### Full installation

Include all optional features:

```bash
pip install -e .[llm,audio,ml,vision,web,network,extras]
```

## Required Packages

The [scripts/check_requirements.sh](../scripts/check_requirements.sh) script expects the following commands to be available:

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

## Environment Variables

Create a `secrets.env` file (copy from `secrets.env.template`) and define:

```bash
HF_TOKEN=<your Hugging Face token>
GLM_API_URL=<GLM endpoint>
GLM_API_KEY=<API key>
```

`secrets.env` is ignored by Git so your credentials stay local.

## Validate Setup

Run the following script from the repository root to verify the configuration:

```bash
scripts/check_requirements.sh
```

The script loads `secrets.env` and confirms that all required commands and variables are present.

