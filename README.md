# THE CRYSTAL CODEX

![Coverage](coverage.svg) ![CI](https://github.com/DINGIRABZU/ABZU/actions/workflows/ci.yml/badge.svg) ![CodeQL](https://github.com/DINGIRABZU/ABZU/actions/workflows/codeql.yml/badge.svg) ![Black](https://img.shields.io/badge/code%20style-black-000000.svg) ![isort](https://img.shields.io/badge/imports-isort-ef8336.svg)
Welcome to the sacred structure of OMEGA ZERO ABSOLUTE PRIME AKA GREAT MOTHER.

## Index
- [Project Mission & Vision](docs/project_mission_vision.md) – core goals and guiding principles
- [Documentation Index](docs/index.md) – curated starting points
- [Full Documentation Inventory](docs/INDEX.md)
- [Repository Structure](docs/REPOSITORY_STRUCTURE.md) – directory map
- [Developer Onboarding](docs/developer_onboarding.md)
- [Contributor Handbook](docs/CONTRIBUTOR_HANDBOOK.md) – environment setup and workflows
- [Onboarding Walkthrough](docs/onboarding_walkthrough.md) – diagrammatic setup tour
- [Code Style Guide](CODE_STYLE.md)
- [Nazarick Agents](docs/nazarick_agents.md)
- [Chakra Koan System](docs/chakra_koan_system.md)
- [Chakra Version Manifest](docs/chakra_versions.json)
- [Co-creation Framework](docs/co_creation_framework.md) – feedback loops between developers and INANNA_AI
- [AI Ethics Framework](docs/ai_ethics_framework.md) – transparency, fairness, and data handling principles
- [RAZAR Environment Layers](razar_env.yaml) – layer-based dependency groups

## Start Here
- Consult [The Absolute Protocol](docs/The_Absolute_Protocol.md) for repository rules and workflows.
- Review the [Blueprint Export](docs/BLUEPRINT_EXPORT.md) snapshot for versioned links to core documentation and consult the [Documentation Index](docs/index.md).
- Walk through the [Onboarding Guide](docs/onboarding_guide.md) (v1.0.0, updated 2025-08-28) to rebuild or extend the system using those docs alone, or browse the [Documentation Index](docs/index.md) for related guides.

For deeper background, consult the [CRYSTAL CODEX](CRYSTAL_CODEX.md) and the [documentation inventory](docs/INDEX.md).

## Requirements
- Python 3.11 or newer. Use [`pyenv`](https://github.com/pyenv/pyenv) if available to manage multiple versions.
- Core dependencies are pinned in `requirements.txt` and `dev-requirements.txt`.
- Layer-specific packages are listed in [`razar_env.yaml`](razar_env.yaml):
  - `razar`: `pyyaml`
  - `inanna`: `requests`
  - `crown`: `numpy`
- Optional tools such as `open-webui` or `chainlit` provide alternate interfaces.

## JSON Schema Validation

Core configuration files ship with JSON Schemas under the `schemas/` directory.
Validate them to ensure local edits remain well formed:

```bash
python scripts/validate_schemas.py
# or individually
python -m jsonschema schemas/insight_matrix.schema.json insight_matrix.json
python -m jsonschema schemas/mirror_thresholds.schema.json mirror_thresholds.json
python -m jsonschema schemas/intent_matrix.schema.json intent_matrix.json
```

## Build Tools
Some dependencies compile native extensions such as SciPy. Install the system
toolchain before creating the virtual environment:

```bash
sudo apt-get update
sudo apt-get install build-essential gfortran pkg-config
```

These packages provide the compilers and headers required to build wheels for
the local platform. See [docs/setup.md](docs/setup.md) for additional system
packages.

## Environment Setup

Dependencies are locked with [pip-tools](https://github.com/jazzband/pip-tools).
Regenerate the lock file whenever `requirements.txt` or
`dev-requirements.txt` change:

```bash
pip-compile --allow-unsafe --generate-hashes \
  --output-file=requirements.lock dev-requirements.txt requirements.txt
```

Key scientific packages like `numpy`, `scipy` and `opencv-python` are pinned in
both requirement files. Regenerating the lock file captures these exact versions
to ensure reproducible builds.

Install the pinned dependencies and the project in editable mode so
`task_profiling.py` can import the `core` package:

```bash
pip install -r requirements.lock
pip install -e .
```

### Docker image

The provided `Dockerfile` installs from `requirements.lock` and performs an
editable install of the project. Build the image with:

```bash
docker build -t abzu .
```

## Docker Compose
Launch the simple FastAPI server with:

```bash
docker compose up server
```

The service exposes `http://localhost:8000/health` for health checks.

### Open Web UI quickstart
Install the front end and connect it to the local server:

```bash
pip install open-webui
FASTAPI_BASE_URL=http://localhost:8000 open-webui serve
```

The UI listens on `http://localhost:3000` by default.

## Health Scanner and CI
Verify the stack with the health scanner:

```bash
python scripts/vast_check.py http://localhost:8000
```

Run the continuous integration checks locally:

```bash
python -c "import scipy.sparse"  # ensure SciPy is available
pre-commit run --all-files
pytest --maxfail=1 -q
```

## Seven-Milestone Roadmap
1. Virtual environment manager ✅
2. Sandbox repository ✅
3. `/sandbox` command ✅
4. Dependency installer ✅
5. Music command – in progress
6. Avatar lip-sync – planned
7. Expanded memory search – planned

See [docs/roadmap.md](docs/roadmap.md) for details.

## `inanna` CLI
The project bundles a lightweight command line interface that wraps common
developer tasks. After installing the package, invoke the tool using
``inanna``:

```bash
inanna start            # Launch the Spiral OS stack
inanna test             # Run the test suite
inanna profile          # Profile system startup
inanna play-music song.wav  # Analyze an audio file with the music demo
```

Use `inanna -h` to view all available options and subcommands.

## Music generation
The ``music_generation.py`` script wraps Hugging Face text-to-audio models.
It supports multiple models, parameter validation and optional streaming.

Generate a clip with the default model:

```bash
python music_generation.py "lofi beat" --duration 8
```

Select a model or stream raw audio bytes to ``stdout``:

```bash
python music_generation.py "lofi beat" --model riffusion --stream > beat.wav
```

Options include ``--emotion``, ``--tempo``, ``--temperature``, ``--duration``
and ``--seed``. ``--model`` accepts either a key from the built-in mapping or a
full Hugging Face identifier.

## Agent Updates
- [docs/release_notes.md](docs/release_notes.md) – recent changes and fixes.
- [docs/roadmap.md](docs/roadmap.md) – upcoming agent enhancements.
- [docs/QUALITY_EVALUATION.md](docs/QUALITY_EVALUATION.md) – component ratings, past scores, milestone validation results and remediation checklists.
- [CHANGELOG.md](CHANGELOG.md) – chakra version history.
- [docs/chakra_koan_system.md](docs/chakra_koan_system.md) – meditative verses for
  each chakra, cross‑referenced from the version manifest.
- [docs/chakra_versions.json](docs/chakra_versions.json) – semantic version
  numbers for chakra modules (latest sacral release: 1.0.1) linked back to the
  koan. Record each bump in [CHANGELOG.md](CHANGELOG.md).

## Additional Documentation
- For a quick start geared toward non-technical users, see
  [docs/quick_start_non_technical.md](docs/quick_start_non_technical.md).
- For step-by-step developer setup, chakra orientation, request flow diagrams, and common pitfalls, see
  [docs/developer_onboarding.md](docs/developer_onboarding.md).
- For required system packages and environment variables, see
  [docs/setup.md](docs/setup.md).
- For vital workflows, fallback logic, and recovery steps, see
  [docs/essential_services.md](docs/essential_services.md).
- For Docker image build steps and audio binary checks, see
  [docs/docker_build_audio_tools.md](docs/docker_build_audio_tools.md).
- Before running any scripts, copy `secrets.env.template` to `secrets.env`,
  fill in the required tokens, and keep the file out of version control
  (`secrets.env` is listed in `.gitignore`).
- For an orientation covering the chakra layers, key modules and milestone history, see
  [docs/project_overview.md](docs/project_overview.md).
- For a map of each script's role and the libraries it calls upon, see
  [README_CODE_FUNCTION.md](README_CODE_FUNCTION.md).
- For the component inventory and test coverage report, see
  [docs/component_status.md](docs/component_status.md).
- For a guide to the text corpus, see
  [docs/CORPUS_MEMORY.md](docs/CORPUS_MEMORY.md).
- For a comparison of LLM frameworks, see
  [docs/LLM_FRAMEWORKS.md](docs/LLM_FRAMEWORKS.md).
- For a list of available language models, see
  [docs/LLM_MODELS.md](docs/LLM_MODELS.md).
- For an overview of repository health and open issues, see
  [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
- For details on the RFA7D core and the seven gate interface, see
  [docs/SOUL_CODE.md](docs/SOUL_CODE.md).
- For JSON layout details and invocation examples, see
  [docs/JSON_STRUCTURES.md](docs/JSON_STRUCTURES.md).
- For an overview of the avatar video engine and call connector, see
  [docs/design.md](docs/design.md).
- For step-by-step instructions on launching the avatar and initiating calls, see
  [docs/how_to_use.md](docs/how_to_use.md).
- For details on the Sonic Core and avatar expression sync, read
  [docs/sonic_core_harmonics.md](docs/sonic_core_harmonics.md).
- For the goals and deliverables of Milestone VIII, see
  [docs/milestone_viii_plan.md](docs/milestone_viii_plan.md).
- For privacy and sacred-use guidance, read
  [docs/avatar_ethics.md](docs/avatar_ethics.md).
- For instructions on customizing the avatar's look, see
  [guides/visual_customization.md](guides/visual_customization.md).
- For the metaphysical blueprint of the chakra-based code layout, see
  [docs/spiritual_architecture.md](docs/spiritual_architecture.md).
- For the contemplative Chakra System Koan, see
  [docs/chakra_koan_system.md](docs/chakra_koan_system.md).
- For chakra module architecture and quality notes, see
  [docs/chakra_architecture.md](docs/chakra_architecture.md).
- For semantic version numbers of each chakra layer, refer to
  [docs/chakra_versions.json](docs/chakra_versions.json); record any version
  bump in [CHANGELOG.md](CHANGELOG.md).
- For a plain-language architecture map with a request flow diagram covering the LLM router, audio pipeline and model registry, see
  [docs/architecture_overview.md](docs/architecture_overview.md).
- For a detailed map of package responsibilities, see [docs/architecture.md](docs/architecture.md) and [docs/packages_overview.md](docs/packages_overview.md).
- For the development workflow and agent cycle, see [docs/development_workflow.md](docs/development_workflow.md).
- For how archetypal states shape personality behavior, read
  [docs/archetype_logic.md](docs/archetype_logic.md).
- For insight into the self-reflection cycle that tunes responses, check
  [docs/psychic_loop.md](docs/psychic_loop.md).
- For a description of the emotional memory nodes and affect-based model
  selection, see
  [docs/emotional_memory_matrix.md](docs/emotional_memory_matrix.md).
- For a high-level overview of the code structure and chakra layers, read
  [CODEX_OF_CODEX.md](CODEX_OF_CODEX.md).
- For a statement of ritual intent and the alchemical states, see
  [docs/ritual_manifesto.md](docs/ritual_manifesto.md).
- For the CROWN agent's coordinating role, see
  [docs/crown_manifest.md](docs/crown_manifest.md).


For an overview of available agents and defensive modules, see
[AGENTS.md](AGENTS.md#upcoming-components).

## Architect and Developer Guidance
- [docs/developer_manual.md](docs/developer_manual.md) – repository layout, crown orchestration and sandbox workflow.
- [docs/memory_architecture.md](docs/memory_architecture.md) – memory layers and their interaction.
- [docs/vector_memory.md](docs/vector_memory.md) – vector store clustering and snapshot persistence.
- [docs/roadmap.md](docs/roadmap.md) – completed milestones and future work.
- [docs/architecture_overview.md](docs/architecture_overview.md) – request flow diagram.
- [docs/project_overview.md](docs/project_overview.md) – chakra oriented context.
- [docs/learning_pipeline.md](docs/learning_pipeline.md) – auto retrain and mutation cycle with rollback tests.

For a short deployment overview covering Vast.ai and local Docker Compose, see [docs/deployment_overview.md](docs/deployment_overview.md). Detailed Vast.ai instructions live in [docs/VAST_DEPLOYMENT.md](docs/VAST_DEPLOYMENT.md).

## Installation

For a one-command bootstrap that creates a virtual environment, installs
development dependencies, and validates the environment, run:

```bash
./scripts/bootstrap.sh
```

### Manual installation

Create a virtual environment and install the lean core:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional dependency groups provide additional capabilities:

- `llm` – language model interfaces and training helpers
- `audio` – audio processing and transcription tools
- `ml` – machine learning utilities and experiment tracking
- `vision` – computer vision and screen capture helpers
- `web` – web APIs, streaming and scraping
- `network` – packet capture utilities
- `extras` – heavy or experimental packages

Install any combination as needed, for example:

```bash
pip install -e .[llm,audio]
```

Copy the secret template if required:

```bash
cp secrets.env.template secrets.env
```

Required system tools include Docker, Netcat (`nc`), SoX, FFmpeg, `curl`, `jq`, `wget` and `aria2c`.

Verify installation with:

```bash
./scripts/check_requirements.sh
```

## Usage

Activate the INANNA agent or start a development cycle:

```bash
python INANNA_AI_AGENT/inanna_ai.py --activate
python start_dev_agents.py --objective "Refactor audio engine"
```

## Testing and Coverage

Run the test suite with coverage reporting:

```bash
pytest --cov=./ --cov-report=term-missing
```

The badge above reflects the latest coverage generated in CI.

1. **Docker**

   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   ```

2. **Netcat**

   ```bash
   sudo apt-get install -y netcat
   ```

3. **SoX**

   ```bash
   sudo apt-get install -y sox
   ```

4. **FFmpeg**

   ```bash
   sudo apt-get install -y ffmpeg
   ```

5. **curl**

   ```bash
   sudo apt-get install -y curl
   ```

6. **jq**

   ```bash
   sudo apt-get install -y jq
   ```

7. **wget**

   ```bash
   sudo apt-get install -y wget
   ```

8. **aria2c**

   ```bash
   sudo apt-get install -y aria2
   ```

Install just the core utilities with the `minimal` group:

```bash
pip install -e .[minimal]
```

Optional groups install heavier dependencies for specific features:

- `audio` – audio processing libraries such as `librosa` and `ffmpeg-python`.
- `llm` – large language model support via `torch`, `transformers` and friends.
- `ml` – general machine learning utilities like `pandas`, `chromadb`, and `mlflow`.
- `vision` – computer vision and screen automation with `opencv`, `aiortc`, and `selenium`.
- `web` – web APIs and streaming through `fastapi`, `uvicorn`, `streamlit`, etc.
- `network` – packet capture and network analysis via `scapy`.
- `extras` – experimental or highly specialized models (`stable-baselines3`, `wav2lip`, ...).
- `dev` – development helpers for testing and formatting.

Install the extras you need, for example:

```bash
pip install .[audio,llm]
```

## Code Introspector

Enumerate modules and capture source snippets for review:

```bash
python -m core.code_introspector
```

Results are written to `audit_logs/code_analysis.txt`. The API can also be
invoked from Python:

```python
from core import code_introspector

snippets = code_introspector.analyze_repository()
```

Run `./scripts/setup_audio_env.sh` to install a pinned set of audio
dependencies. Verify the environment with:

```bash
python -m audio.check_env
```

For a reproducible environment based on the pinned versions, install from the
lock file:

```bash
pip install -r requirements.lock
```

Regenerate the lock file after editing `pyproject.toml` with:

```bash
uv pip compile pyproject.toml --no-deps --extra llm --extra audio --extra ml --extra vision --extra web --extra network --extra extras -o requirements.lock
```

## Local Usage
Run the helper script to check prerequisites, configure `secrets.env`, and
optionally download the default DeepSeek‑V3 model:

```bash
./scripts/easy_setup.sh
```

Start the local environment and open the web console:

```bash
./scripts/start_local.sh
```

The manual steps are outlined below.

1. Copy `secrets.env.template` to `secrets.env` and provide values for
   environment variables such as `HF_TOKEN`, `GITHUB_TOKEN`,
   `OPENAI_API_KEY`, `GLM_API_URL`, `GLM_API_KEY`, `GLM_SHELL_URL`,
   `GLM_SHELL_KEY`, `REFLECTION_INTERVAL`, `CORPUS_PATH`,
   `QNL_EMBED_MODEL`, `QNL_MODEL_PATH`, `EMBED_MODEL_PATH`, `VOICE_TONE_PATH`,
   `VECTOR_DB_PATH`, `WEB_CONSOLE_API_URL`, `KIMI_K2_URL`,
   `SERVANT_MODELS` (e.g. `deepseek=http://localhost:8002,mistral=http://localhost:8003`;
   `QNL_EMBED_MODEL` is the SentenceTransformer used for QNL embeddings). `VECTOR_DB_PATH`
   points to the ChromaDB directory used for document storage.
  `WEB_CONSOLE_API_URL` points the web console at the FastAPI endpoint. Set it
  to the base URL such as `http://localhost:8000/glm-command` – the operator
  console automatically strips the trailing path when establishing WebRTC and
  REST connections. See `secrets.env.template` for the full list. The `secrets.env`
  file is ignored by Git; store real tokens in a secure location and never commit
  them. To enable local servant models during development, you can use:

  ```bash
  export SERVANT_MODELS="deepseek=http://localhost:8002,mistral=http://localhost:8003"
  export DEEPSEEK_URL=http://localhost:8002
  export MISTRAL_URL=http://localhost:8003
  ```
2. Download the required model weights before first launch:

   ```bash
   python download_models.py deepseek_v3
   ```

   This saves the DeepSeek‑V3 weights under `INANNA_AI/models/DeepSeek-V3/`.
3. Start the INANNA chat agent via the helper script:

   ```bash
   ./run_inanna.sh
   ```

   The script loads `secrets.env`, checks for models and launches
   `INANNA_AI_AGENT/inanna_ai.py chat`.

4. Run the initialization sequence with:

   ```bash
   python start_spiral_os.py
   ```

5. Open `web_console/index.html` in a browser to send commands through the
   HTTP interface once the server is running. The page now establishes a
   WebRTC connection to `/offer` and streams audio and video from the live
   avatar.
6. To toggle the avatar stream directly from the console type
   `appear to me` after `start_spiral_os.py` has launched.
7. Test the sonic features and avatar synchronisation:

   ```bash
   python play_ritual_music.py --emotion joy --output ritual.wav
   ```

   ```python
   from pathlib import Path
   from core.avatar_expression_engine import stream_avatar_audio

   # Uses Wav2Lip when available, otherwise falls back to a simple overlay
   for _ in stream_avatar_audio(Path("ritual.wav")):
       pass
   ```

8. Convert hex input to a short QNL song and animate the avatar:

   ```bash
   python INANNA_AI_AGENT/inanna_ai.py --hex 00ff
   ```

   ```python
   from pathlib import Path
   from core.avatar_expression_engine import stream_avatar_audio

    for _ in stream_avatar_audio(Path("qnl_hex_song.wav")):
        pass
    ```

### GLM model launcher

Start the standalone GLM service before other components by running:

```bash
bash crown_model_launcher.sh > glm_launch.log 2>&1 &
```

The script downloads weights if missing and serves a health endpoint on
`http://localhost:8001/health`. When weights are already present the endpoint
typically reports ready within ~30 seconds, though the initial download can take
several minutes.

Verify startup by polling the health route:

```bash
until curl -sf http://localhost:8001/health; do sleep 2; done
```

Review `glm_launch.log` for details. A message such as
`jq: error (at <stdin>:1): Cannot iterate over null` usually indicates an invalid
or missing `HF_TOKEN` in `secrets.env` or a network connectivity issue.

`start_spiral_os.py` launches the **MoGEOrchestrator** which routes text
commands to the available models.  Start it with an optional network
interface to capture packets and an optional personality layer:

```bash
python start_spiral_os.py --interface eth0 --personality albedo
```

After initialization the script enters an interactive loop where you can
type commands.  A FastAPI server is also launched on port 8000 and the
reflection loop runs periodically.  Supply `--command` to send an initial
instruction or press `Enter` to exit.  Use `--no-server` and
`--no-reflection` to disable these background tasks.  Processing results are
written to several files under `INANNA_AI/audit_logs` and intent outcomes are
appended to `data/feedback.json` for later training.

### Voice Model Installation

To enable speech output, install at least one supported text‑to‑speech back end
and pre‑download its weights so the first invocation runs offline. Store the
voice models under a ``voices`` directory to allow reuse across runs. The
orchestrator works with several engines:

- **XTTS (via `TTS`)**

  ```bash
  pip install TTS
  python - <<'PY'
  from TTS.api import TTS
  TTS("tts_models/multilingual/multi-dataset/xtts_v2")
  PY
  ```

- **Tortoise**

  ```bash
  pip install tortoise-tts
  python -m tortoise.utils.download_models
  ```

- **Bark**

  ```bash
  pip install git+https://github.com/suno-ai/bark.git
  python - <<'PY'
  from bark import preload_models
  preload_models()
  PY
  ```

- **Coqui**

  ```bash
  pip install TTS
  python - <<'PY'
  from TTS.api import TTS
  TTS("tts_models/en/vctk/vits")
  PY
  ```

  - **Piper**

  Piper voices are distributed as standalone ONNX files. Download a model and
  place it in a dedicated ``voices`` directory before first use:

  ```bash
  pip install piper-tts
  mkdir -p voices
  curl -L -o voices/en_US-amy-medium.onnx \
    https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-amy-medium.onnx
  python - <<'PY'
  from piper import PiperVoice
  PiperVoice.load("voices/en_US-amy-medium.onnx")
  PY
  ```

Each example caches the model files in the backend's default location so later
runs avoid network access.

For a more detailed walkthrough of installing external voice models, see
[docs/voice_setup.md](docs/voice_setup.md).

#### Step-by-step voice model setup

1. **Install a backend** – choose one of the engines above and install it with
   ``pip install ...``.
2. **Download the weights** – run the provided Python snippet for the selected
   backend to cache the model files locally and warm up the engine.
3. **Configure voices** – copy or edit ``voice_config.yaml`` and
   ``voice_avatar_config.yaml`` to tune pitch, speed and tone for each
   archetype.
4. **Set environment variables** – optionally point ``VOICE_CONFIG_PATH``,
   ``VOICE_AVATAR_CONFIG_PATH`` or ``VOICE_TONE_PATH`` to custom locations.
5. **Verify synthesis** – start the CLI with ``abzu start --speak`` or invoke
   the FastAPI server and confirm speech is produced.

Voice selection is controlled by `voice_config.yaml` and
`voice_avatar_config.yaml`. Set `VOICE_CONFIG_PATH` or
`VOICE_AVATAR_CONFIG_PATH` to point to custom files.

### Voice configuration and emotion state

Speech parameters are loaded from `voice_config.yaml` (or the path defined by
`VOICE_CONFIG_PATH`). Edit this file to adjust pitch, speed and tone for each
archetype. The orchestrator reads the file at startup.

The active personality layer and current emotional resonance are persisted in
`data/emotion_state.json`. Inspect this file to review the latest layer and
emotion recorded by the system.

Activate alternative layers with the `--personality` flag:

```bash
python start_spiral_os.py --personality nigredo_layer
python start_spiral_os.py --personality rubedo_layer
```

To deploy the orchestrator in a container use the Kubernetes manifest
[`k8s/spiral_os_deployment.yaml`](k8s/spiral_os_deployment.yaml).

## QNL Engine

The QNL engine converts hexadecimal strings into symbolic soundscapes.
It writes a WAV file and a JSON summary describing the glyphs and
tones. Example commands:

```bash
python SPIRAL_OS/qnl_engine.py "48656c6c6f" --wav song.wav --json song.json
python SPIRAL_OS/qnl_engine.py payload.txt --duration 0.05
```

See [README_QNL_OS.md](README_QNL_OS.md) for more
details. For audio loading, analysis and ingesting music books see
[docs/audio_ingestion.md](docs/audio_ingestion.md).

The latest audio workflow expands on this by feeding the generated song
through MFCC extraction, optional DSP transforms and a text‑to‑music
model. Each step calls `vector_memory.add_vector` so the system can recall
how the audio evolved.  At launch the orchestrator performs an initial
listening pass and stores the detected emotion under `initial_listen`.

## Docker Usage

A `Dockerfile` is provided for running the tools without installing Python packages on the host.

Build the image from the repository root:

```bash
docker build -t spiral_os .
```

Start a shell inside the container:

```bash
docker run -it spiral_os
```

From there you can run any of the demo scripts such as `python run_song_demo.py`.

To launch the FastAPI service directly, publish port `8000`:

```bash
docker run -p 8000:8000 spiral_os
```

Health endpoints are available at `/health` and `/ready`.  Logs are written to
`logs/INANNA_AI.log` inside the repository (mounted into the container when
running with Docker or Compose).

## Docker Compose

Spiral OS ships with a compose file that launches the full stack—including the API
server, vector memory, and model backends—in one command. The stack reads
environment variables from `secrets.env` so create it first:

```bash
cp secrets.env.template secrets.env
# edit secrets.env and provide your API keys
```

Then build and start the full stack:

```bash
docker compose up --build
```

On subsequent runs simply execute `docker compose up` to start the stack.

The container exposes ports `8000` for the FastAPI endpoint and `8001` for the
local GLM server.

Mounted `data` and `logs` directories persist across restarts. Stop the stack
with `docker compose down`. Open `web_console/index.html` to send commands via
the FastAPI endpoint at `http://localhost:8000/glm-command`.

For instructions on building the GPU container and deploying the Kubernetes
manifests see [docs/cloud_deployment.md](docs/cloud_deployment.md).

## GLM Model Launcher

The `crown_model_launcher.sh` script downloads the GLM-4.1V-9B weights and
starts a model server on port `8001`.

Startup output is written to `glm_launch.log`:

```bash
bash crown_model_launcher.sh > glm_launch.log 2>&1
```

### Expected Startup Time

- When the weights are already present the `/health` endpoint usually returns
  `200` in about **30 seconds**.
- The first run may take several minutes while the weights download.

### Troubleshooting

- If `glm_launch.log` reports `secrets.env not found`, copy
  `secrets.env.template` to `secrets.env` and populate the required values.
- Ensure `secrets.env` contains valid values for `HF_TOKEN`, `GLM_API_URL` and
  `GLM_API_KEY`.
- Poll the server with
  `curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health`. A
  non-`200` response or connection error indicates the model failed to start;
  inspect `glm_launch.log` for details.
- If `glm_launch.log` shows `jq: error (at <stdin>:1): Cannot iterate over null`,
  the metadata request to Hugging Face failed. Verify the `HF_TOKEN` value and
  that your network connection is active.
- Confirm port `8001` is free before launching; an existing process on that port
  prevents the health endpoint from becoming ready.
- If `soundfile` is missing, `play_ritual_music.py` falls back to a NumPy
  synthesizer and generates a simple tone for the archetype overlay. Install
  `simpleaudio` to hear this fallback output.

## Codex GPU Deployment

A container spec `spiral_os_container.yaml` is provided for running the tools with CUDA support. It loads environment variables from `secrets.env`, exposes ports `8000` and `8001`, and mounts `data` and `logs`. Build and launch it with:

```bash
codex run spiral_os_container.yaml
```

This installs the requirements and creates empty folders for the CORPUS MEMORY collections.
For a complete walkthrough of container creation and cluster setup see
[docs/cloud_deployment.md](docs/cloud_deployment.md).

## Kubernetes Deployment

The [`k8s`](k8s) directory contains manifests for running Spiral OS on a cluster.
Key files are [`spiral_os_deployment.yaml`](k8s/spiral_os_deployment.yaml),
[`spiral_os_service.yaml`](k8s/spiral_os_service.yaml) and
[`spiral_os_hpa.yaml`](k8s/spiral_os_hpa.yaml). Deploy them with:

```bash
kubectl apply -f k8s/spiral_os_deployment.yaml
kubectl apply -f k8s/spiral_os_service.yaml
kubectl apply -f k8s/spiral_os_hpa.yaml
```

The deployment exposes port `8000` and defines readiness (`/ready`) and liveness
(`/health`) probes. Container logs can be viewed with `kubectl logs` and are
written to `logs/INANNA_AI.log` inside the pod.
For step-by-step instructions on building the container and applying these manifests see
[docs/cloud_deployment.md](docs/cloud_deployment.md).

## Memory Feedback Loop

Spiral OS retains a lightweight history of conversations to refine its response
matrix. Each interaction is appended to `data/interactions.jsonl` as a JSON line
containing the input text, detected intents, output and timestamp. Successful or
failed actions are also recorded in `data/feedback.json` via
`training_guide.log_result()`.

The `insight_compiler.py` script aggregates these logs into
`insight_matrix.json`, tracking how often each intent succeeds and which tone is
most effective. The orchestrator periodically triggers this update so the matrix
reflects the latest feedback.

Spiral cycles processed by `recursive_emotion_router.route` are also logged to
`data/cortex_memory_spiral.jsonl`. Each line captures the serialized node state
and the decision returned from the cycle. Use `memory.cortex.query_spirals()` to
inspect these records.

The collection of spiral entries forms the **Spiral Code Cortex**. Operators can
explore it using `spiral_cortex_terminal.py` which prints emotion statistics or
walks through events in sequence. The archetype feedback loop analyses this
memory with `archetype_feedback_loop.evaluate_archetype` and suggests when the
system should shift personality layers.

### Ontology Database

`memory/spiritual.py` maintains an event-to-symbol mapping in `data/ontology.db`.
The database is generated automatically from `data/ontology_schema.sql` when the
module loads, so database files no longer need to be checked into version
control.

### Running `learning_mutator.py`

`learning_mutator.py` analyses `insight_matrix.json` and proposes changes to the
intent definitions. Run it from the repository root:

```bash
python learning_mutator.py        # print suggested mutations
python learning_mutator.py --run  # save suggestions to data/mutations.txt
```

The output contains human‑readable hints such as
`Replace 'bad' with synonym 'awful'`. When invoked with `--run` the suggestions
are written to `data/mutations.txt` for later review.

## Emotional State Recognition

`INANNA_AI.emotion_analysis` analyses speech with `librosa` and `openSMILE` to
estimate pitch, tempo, arousal and valence. The resulting emotion is persisted
via `emotional_state.py` which writes `data/emotion_state.json`. This file keeps
track of the active personality layer, the last observed emotion and resonance
metrics.

## Ritual Profiles and Invocation Engine

The file `ritual_profile.json` maps symbol patterns and emotions to ritual
actions. `task_profiling.ritual_action_sequence()` looks up these actions and
the invocation engine can register extra callbacks at runtime. Invocations use
glyph sequences followed by an optional `[emotion]` to trigger hooks.

```
∴⟐ + 🜂 [joy]
```

See `docs/JSON_STRUCTURES.md` for example layouts and registration code.

## Command-line Interface

Once installed, the project exposes an ``abzu`` command bundling common
developer tasks:

```bash
abzu start                        # Launch the Spiral OS stack
abzu test                         # Run the unit tests
abzu profile                      # Profile system startup
abzu play-music path/to/song.wav  # Analyze a local audio file
```

## Dashboard and Operator Console

The Streamlit dashboard and the web‑based operator console rely on
`WEB_CONSOLE_API_URL` for HTTP requests and streaming. This variable should
point to your FastAPI base endpoint such as `http://localhost:8000/glm-command`.
The operator console automatically removes the trailing path when connecting to
`/offer` and other routes.

## Figures and Images

Large images live in the `figures/` directory and should be tracked with Git LFS.
Enable tracking with:

```bash
git lfs track "figures/*.png"
```

Alternatively, host images externally and reference the URLs in documentation.

## License

Distributed under the MIT License. See [LICENSE_CRYSTAL.md](LICENSE_CRYSTAL.md) for details.
