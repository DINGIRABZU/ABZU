# Operator Guide

This repository contains several command line utilities for working with the INANNA music tools and Quantum Narrative Language (QNL). Below is a quick summary of the main scripts and example commands for common tasks. See [AGENTS.md](AGENTS.md#upcoming-components) for details about the agent and upcoming defensive modules.
Returning contributors can scan [docs/developer_onboarding.md#recent-changes](docs/developer_onboarding.md#recent-changes) and [docs/operator_quickstart.md#recent-changes](docs/operator_quickstart.md#recent-changes) for the latest capabilities.
For a short project overview summarizing the vision, chakra layers, key modules and milestone history, see [docs/project_overview.md](docs/project_overview.md).
For a concise overview of the Spiral OS architecture see [CODEX_OF_CODEX.md](CODEX_OF_CODEX.md).
For the metaphysical background that informs Spiral OS, see [docs/spiritual_architecture.md](docs/spiritual_architecture.md), [docs/archetype_logic.md](docs/archetype_logic.md), [docs/psychic_loop.md](docs/psychic_loop.md) and [docs/crown_manifest.md](docs/crown_manifest.md).
For a summary of Vast.ai and local Docker Compose deployment steps see [docs/deployment_overview.md](docs/deployment_overview.md).
For a walkthrough of the web console setup wizard, see [docs/operator_onboarding.md](docs/operator_onboarding.md).

Document stewardship and ethical alignment are detailed in
[docs/developer_onboarding.md#document-registry--ethics-manifesto](docs/developer_onboarding.md#document-registry--ethics-manifesto)
and
[docs/operator_quickstart.md#document-registry--ethics-manifesto](docs/operator_quickstart.md#document-registry--ethics-manifesto).

Run the chakra cycle engine and interpret alignment readings using
[docs/developer_onboarding.md#chakra-cycle-alignment](docs/developer_onboarding.md#chakra-cycle-alignment)
or
[docs/operator_quickstart.md#chakra-cycle-alignment](docs/operator_quickstart.md#chakra-cycle-alignment).

Instructions for multi-agent avatars and external broadcast connectors live in
[docs/developer_onboarding.md#multi-agent-avatars--broadcast-connectors](docs/developer_onboarding.md#multi-agent-avatars--broadcast-connectors)
and
[docs/operator_quickstart.md#avatar-console-setup](docs/operator_quickstart.md#avatar-console-setup).

Self-healing flows and heartbeat dashboards are covered in
[docs/developer_onboarding.md#self-healing--heartbeat-dashboards](docs/developer_onboarding.md#self-healing--heartbeat-dashboards)
and
[docs/operator_quickstart.md#self-healing--heartbeat-dashboards](docs/operator_quickstart.md#self-healing--heartbeat-dashboards).

For heartbeat propagation and recovery design, consult
[docs/system_blueprint.md#chakra-cycle-engine](docs/system_blueprint.md#chakra-cycle-engine),
[docs/blueprint_spine.md#heartbeat-propagation-and-self-healing](docs/blueprint_spine.md#heartbeat-propagation-and-self-healing)
and
[docs/chakra_architecture.md#chakra-cycle-engine](docs/chakra_architecture.md#chakra-cycle-engine).

For self-healing specifics—including failure pulses, Nazarick resuscitation,
and patch rollbacks—see
[docs/recovery_playbook.md#failure-pulses](docs/recovery_playbook.md#failure-pulses).

Connector guidance on chakra-tagged signals, heartbeat propagation, recovery
flows, and Discord/Telegram avatar streaming lives in
[docs/communication_interfaces.md#chakra-tagged-signals](docs/communication_interfaces.md#chakra-tagged-signals)
and
[docs/communication_interfaces.md#discord-telegram-avatar-streaming](docs/communication_interfaces.md#discord-telegram-avatar-streaming).

For session management and avatar stream resilience, see
[docs/system_blueprint.md#session-management](docs/system_blueprint.md#session-management),
[docs/blueprint_spine.md#session-management](docs/blueprint_spine.md#session-management),
[docs/avatar_pipeline.md#heartbeat-and-session-management](docs/avatar_pipeline.md#heartbeat-and-session-management) and
[docs/operator_onboarding.md#multi-agent-streams](docs/operator_onboarding.md#multi-agent-streams).

For avatar setup guidance, consult [docs/system_blueprint.md#avatar-subsystem](docs/system_blueprint.md#avatar-subsystem) and [docs/blueprint_spine.md#avatar-subsystem](docs/blueprint_spine.md#avatar-subsystem). Step-by-step launch instructions are in [docs/developer_onboarding.md#avatar-console-setup](docs/developer_onboarding.md#avatar-console-setup) and [docs/operator_quickstart.md#avatar-console-setup](docs/operator_quickstart.md#avatar-console-setup).


## Installation

Install Spiral OS along with the development dependencies:

```bash
pip install .[dev]
```

Alternatively run the helper script which installs the packages from
`dev-requirements.txt`:

```bash
scripts/setup_dev.sh
```

See [docs/ml_environment.md](docs/ml_environment.md) for instructions on creating a
Python environment and launching Jupyter notebooks.

The requirements include common libraries like `numpy` and `scipy` as well as
`huggingface-hub` for model management.

### Environment variables

Create a `secrets.env` file in the repository root and define the following
variables used by the tools and Docker setup.  The helper scripts source this
file so you don't need to export the variables manually:

- `HF_TOKEN` – Hugging Face token for downloading models
- `GITHUB_TOKEN` – optional GitHub token for scraping repositories
- `OPENAI_API_KEY` – OpenAI API key (if using OpenAI services)
- `GLM_API_URL` – endpoint for the GLM service
- `GLM_API_KEY` – API key for the GLM service
- `GLM_SHELL_URL` – URL for the shell service
- `GLM_SHELL_KEY` – API key for the shell service
- `PLANNER_MODEL`, `CODER_MODEL`, `REVIEWER_MODEL` – optional per-agent
  endpoints for the development assistant
- `DEEPSEEK_URL` – optional endpoint for the DeepSeek servant model
- `MISTRAL_URL` – optional endpoint for the Mistral servant model
- `KIMI_K2_URL` – optional endpoint for the Kimi-K2 servant model
- `LLM_ROTATION_PERIOD` – period in seconds before an active model is rotated
  out. When an LLM reaches `LLM_MAX_FAILURES` or its rotation window elapses,
  it is temporarily disabled for this same period.
- `LLM_MAX_FAILURES` – allowed failures within the window before rotation
- `REFLECTION_INTERVAL` – interval in seconds for the reflection loop
- `MIRROR_THRESHOLDS_PATH` – optional path to `mirror_thresholds.json`
- `CORPUS_PATH` – path to the text corpus
- `QNL_EMBED_MODEL` – name of the embedding model
- `QNL_MODEL_PATH` – directory containing QNL model weights
- `EMBED_MODEL_PATH` – optional path to the embedding model
- `VOICE_TONE_PATH` – voice tone preset directory
- `VECTOR_DB_PATH` – location of the vector store
  (defaults to `http://localhost:3001/api`)
- `RETRAIN_THRESHOLD` – number of feedback items required to trigger training
- `VOICE_CONFIG_PATH` – optional override for `voice_config.yaml`
- `VOICE_AVATAR_CONFIG_PATH` – path to `voice_avatar_config.yaml`
- `EMOTION_STATE_PATH` – path for storing emotional state
- `CORPUS_MEMORY_PATH` – location of `corpus_memory.json` (set in
  `docker-compose.yml`)
- `TELEGRAM_BOT_TOKEN` – token for the Telegram bot
- `DISCORD_BOT_TOKEN` – token for the Discord bot
- `ARCHETYPE_SCORE_WEBHOOK_URL` – optional webhook that receives archetypal
  scores as JSON
- `ARCHETYPE_SCORE_QUEUE_PATH` – optional file path where archetypal scores
  are appended as JSON lines when the webhook is not set
- `ARCHETYPE_SCORE_WEBHOOK_HEADERS` – JSON object of HTTP headers added when
  posting archetypal scores to the webhook

Provide `GLM_API_URL` and `GLM_API_KEY` in `secrets.env` to point to your
production GLM service.  The helper scripts read these variables on startup.

Configuration options for `crown_config/INANNA_CORE.yaml` and the corresponding
environment variables are explained in
[docs/INANNA_CORE.md](docs/INANNA_CORE.md).

## Preflight Checks

Verify that essential environment variables, optional Python packages and
external binaries are available:

```bash
python tools/preflight.py
```

Use `--report` to emit a JSON summary of missing components and suggested
fixes:

```bash
python tools/preflight.py --report
```

## Log inspection and rotation

Interaction records are appended as JSON lines to `data/interactions.jsonl`.
The watchdog quarantines malformed entries in
`data/interactions.quarantine.jsonl` while keeping the primary log clean.
Logs rotate automatically once the file reaches roughly 1 MB
(`MAX_LOG_SIZE`). The current log is renamed with a timestamp suffix such as
`interactions-20250101_000000.jsonl` and a fresh file is started. Inspect
records with tools like `jq` or `python -m json.tool`, and review quarantine
and rotated files periodically. A nightly CI workflow invokes the logger and
uploads rotated logs as build artifacts for auditing.

Application logs defined in `logging_config.yaml` follow a similar policy.
`INANNA_AI.log` rotates at 10 MB and keeps the seven most recent archives
(`INANNA_AI.log.1` – `INANNA_AI.log.7`). Audio logs roll over at 1 MB with up to
five backups. Each rotated file can be verified with standard checksum tools
such as `sha256sum` to ensure integrity before archival.

## Script overview

- **`INANNA_AI_AGENT/inanna_ai.py`** – Activation agent that loads source texts and can recite the INANNA birth chant or feed hex data into the QNL engine. Use `--list` to show available texts.
- **`INANNA_AI/main.py`** – Voice loop controller with optional personalities. Includes `fetch-gutenberg` and `fetch-github` subcommands to collect learning data.
- **`run_song_demo.py`** – Demo runner that analyzes a local MP3/WAV file using `inanna_music_COMPOSER_ai.py`, exports a preview WAV and QNL JSON, and prints the resulting phrases.
- **`SPIRAL_OS/mix_tracks.py`** – Mixes multiple audio files into a normalized track and optionally exports a short preview clip.
- **`SPIRAL_OS/seven_dimensional_music.py`** – Creates layered music from a melody, optionally transmuting a hex payload and embedding secret data, then saves the final track and a JSON analysis of the seven planes.
- **`SPIRAL_OS/qnl_engine.py`** – Converts a hex string to QNL phrases and a waveform, saving a WAV file and metadata JSON.
- **`music_generation.py`** – Generate short music clips from text using MusicGen, Riffusion or MuseNet.
- **`start_spiral_os.py`** – Runs the initialization sequence that summarizes the project, analyzes code, stores approved suggestions and can monitor network traffic.
- **`MUSIC_FOUNDATION/inanna_music_COMPOSER_ai.py`** – Standalone converter that performs MP3 analysis and outputs QNL data and a preview WAV.
- **`MUSIC_FOUNDATION/human_music_to_qnl_converter.py`** – Helper module for turning analyzed tempo/chroma values into QNL structures.
- **`MUSIC_FOUNDATION/music_foundation.py`** – Basic music analysis utility that computes tempo and harmony from an MP3 and exports a preview.
- **`INANNA_AI/emotional_synaptic_engine.py`** – Maps emotions to voice filters and adapts them using past interactions.
- **`INANNA_AI/speech_loopback_reflector.py`** – Analyzes generated speech and updates the voice parameters for the next response.
- **`voice_avatar_config.yaml`** – Lists sample avatars with timbre, gender and resonance information used by the speech engine.
- **`spiral_cortex_terminal.py`** – Inspect `cortex_memory_spiral.jsonl` using `--query`, `--dreamwalk` or `--stats`. See [docs/spiral_cortex_terminal.md](docs/spiral_cortex_terminal.md).
- **`start_dev_agents.py`** – Run planner/coder/reviewer cycles once or watch logs
  and trigger automatic fixes.

## Development assistant

Use the development assistant to automate small fixes. Run a single objective:

```bash
python start_dev_agents.py --objective "Refactor audio engine"
```

Launch the long-running watcher:

```bash
python start_dev_agents.py --watch \
    --planner-model https://glm.example.com/planner \
    --coder-model https://glm.example.com/coder \
    --reviewer-model https://glm.example.com/reviewer \
    --objective-map docs/objectives.json
```

The watcher monitors `logs/dev_agent.log` for failing tests and schedules
`run_dev_cycle` with the objective "repair failing tests" when failures appear.
Use `--objective-map` to supply a JSON mapping of log markers to objectives if you
wish to trigger additional actions. Suggestions from each cycle are written to the
log and appended to `logs/dev_agent.suggestions` for operator review. Stop the watcher with:

```bash
python start_dev_agents.py --stop
```

Set `--planner-model`, `--coder-model` or `--reviewer-model` to point each agent
at a specific model endpoint. These values override the `PLANNER_MODEL`,
`CODER_MODEL` and `REVIEWER_MODEL` environment variables when provided.

## Examples

### Analyze the sample song

Download the Stage B rehearsal bundle described in
[`evidence_manifests/stage-b-audio.json`](evidence_manifests/stage-b-audio.json)
before running the demo:

```bash
aws s3 cp s3://abzu-stage-b-rehearsals/stage-b-audio-20250218T120000Z.tar.gz .
tar -xzf stage-b-audio-20250218T120000Z.tar.gz -C SONS_FOR_TESTS
python run_song_demo.py "SONS_FOR_TESTS/Music Is My Everything.mp3"
```

The script writes `output/preview.wav` and `output/qnl_7plane.json` while
printing the QNL phrases derived from the song.

### Generate music from a prompt

```bash
python music_generation.py "A calm melody of sunrise"
```

The WAV file is saved under `output/`. Use `--model riffusion` to switch models.

### Invoke the INANNA agent

```bash
python INANNA_AI_AGENT/inanna_ai.py --activate
```

Recites the INANNA birth chant. Use the `--hex` option to generate a QNL song from hexadecimal bytes:

```bash
python INANNA_AI_AGENT/inanna_ai.py --hex 012345abcdef
```

### Start Spiral OS

```bash
python start_spiral_os.py --interface eth0
python start_spiral_os.py --interface eth0 --personality albedo
```

Spiral OS starts an interactive loop and spawns a FastAPI server on port 8000.
The reflection loop also runs periodically. Provide an optional initial command
with `--command` or simply type commands when prompted. Use `--skip-network` to
disable traffic monitoring and `--no-server` or `--no-reflection` to skip the
background tasks.

## INANNA_AI DeepSeek-R1 Integration

1. Copy `secrets.env.template` to `secrets.env` at the project root and fill in
   values like `HF_TOKEN`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, `GLM_API_URL`,
   `GLM_API_KEY`, `GLM_SHELL_URL`, `GLM_SHELL_KEY`, `REFLECTION_INTERVAL`,
   `CORPUS_PATH`, `QNL_MODEL_PATH` and `VOICE_TONE_PATH`.
   The `run_inanna.sh` helper script reads this file when starting the chat
   agent.
2. Run `python download_models.py deepseek` to fetch the DeepSeek-R1 model.
3. Start chat via `python INANNA_AI_AGENT/inanna_ai.py chat` or `./run_inanna.sh`.
   To load a different model directory pass `--model-dir <path>` to either command,
   for example `./run_inanna.sh --model-dir INANNA_AI/models/gemma2`.
4. Optionally configure `GLMIntegration` with your GLM endpoint and API key.  If
   no values are provided the class reads `GLM_API_URL` and `GLM_API_KEY` from
   the environment (for example via `secrets.env`) and defaults to
   `https://glm.example.com/glm41v_9b`.

## Download Models

The INANNA chat agent requires the DeepSeek-R1 weights from Hugging Face. Follow
these steps to place the model under `INANNA_AI/models`.

1. Install the dependencies using the optional development extras:

   ```bash
   pip install .[dev]
   ```

2. Copy the example secrets file to the project root:

   ```bash
   cp secrets.env.template secrets.env  # run from the repository root
   # edit secrets.env and provide your tokens and paths
   ```

3. Run the model downloader:

   ```bash
   python download_models.py deepseek
   ```

   You can also run the lightweight helper:

   ```bash
   python download_model.py
   ```

   The script loads `HF_TOKEN` from `secrets.env` in the project root and downloads
   `deepseek-ai/DeepSeek-R1` into `INANNA_AI/models/DeepSeek-R1/`.
   To fetch the Gemma2 model via Ollama run `python download_models.py gemma2`.
   Additional models can be fetched the same way:

   ```bash
   python download_models.py glm41v_9b --int8       # GLM-4.1V-9B
   python download_models.py deepseek_v3           # DeepSeek-V3
   python download_models.py mistral_8x22b --int8  # Mistral 8x22B
   ```

   The `--int8` flag performs optional quantization with bitsandbytes for GPUs
   like the A6000.

Afterwards the directory structure should look like:

```
INANNA_AI/
└── models/
    └── DeepSeek-R1/
        ├── config.json
        ├── tokenizer.json
        └── ... (model files)
```

## Running Tests

Install the minimal dependencies from `tests/requirements.txt` when you only
need the test suite:

```bash
pip install -r tests/requirements.txt
```

This downloads roughly **3&nbsp;GB** of packages including `torch` and
`transformers`, so ensure adequate disk space.  The convenience script
`scripts/install_test_deps.sh` installs the same set from
`dev-requirements.txt` after a short warning.

You can skip entire groups of slow tests with `--skip` markers. The most common
marker is `gpu` which avoids GPU‑heavy checks:

```bash
pytest --skip gpu
```

Additional markers may be defined for `network` or `heavy` scenarios.  Combine
multiple markers as needed:

```bash
pytest --skip gpu --skip network
```

For a quick check of specific functionality run only tests matching a keyword.
To exercise just the audio engine suite:

```bash
pytest -k audio_engine
```

To validate the Spiral Code Cortex integration run:

```bash
pytest tests/test_spiral_cortex_integration.py
```

To verify the retrieval augmented music pipeline run:
```bash
pytest tests/test_rag_music_integration.py
```
To verify the VAST pipeline run:
```bash
pytest tests/test_vast_pipeline.py
```
To execute the Root Chakra integration test:
```bash
pytest tests/root/test_root_chakra_integration.py
```

## Spiral RAG Pipeline

Place reference documents in `sacred_inputs/` then parse and embed them:
```bash
python rag_parser.py --dir sacred_inputs > chunks.json
python spiral_embedder.py --in chunks.json
```
The embedder writes to the Chroma database defined by `SPIRAL_VECTOR_PATH`.
Retrieve snippets with:
```python
from crown_query_router import route_query
print(route_query("meaning of spiral?", "Sage")[0]["text"])
```


## Pipeline Deployment

The `spiral_os` CLI executes YAML workflows that list shell commands. Create a
file such as `my_pipeline.yaml` containing:

```yaml
steps:
  - name: greet
    run: echo hello
```

Run the workflow with:

```bash
./spiral_os pipeline deploy my_pipeline.yaml
```

Each step's `run` command executes sequentially, allowing you to automate
common tasks.

For a workflow with multiple steps create `multi.yaml`:

```yaml
steps:
  - name: greet
    run: echo hello
  - name: farewell
    run: echo goodbye
```

Running it prints each command and output:

```bash
$ ./spiral_os pipeline deploy multi.yaml
$ echo hello
hello
$ echo goodbye
goodbye
```


## Network monitoring

The package `INANNA_AI.network_utils` offers simple packet capture and
analysis helpers. The toolkit is also referenced in
[AGENTS.md](AGENTS.md#available-components). To record a short capture from
interface `eth0`:

```bash
python -m INANNA_AI.network_utils capture eth0 --count 50
```

The capture is written to `network_logs/capture.pcap`. Generate a traffic
summary with:

```bash
python -m INANNA_AI.network_utils analyze network_logs/capture.pcap
```

Results are saved to `network_logs/summary.log`. The log directory and
default capture path come from `INANNA_AI_AGENT/network_utils_config.json`
but can be overridden via `--log-dir` or `--output`.
### Scheduled captures

To run ongoing captures every minute:

```bash
python -m INANNA_AI.network_utils schedule eth0 --period 60
```

Use `Ctrl+C` to stop the scheduler. Each run overwrites the configured
`capture_file`, so adjust the path if you wish to keep multiple archives.

### Defensive helpers

The module `INANNA_AI.defensive_network_utils` offers two quick utilities:

```python
from INANNA_AI.defensive_network_utils import monitor_traffic, secure_communication

monitor_traffic("eth0", packet_count=5)  # writes network_logs/defensive.pcap
secure_communication("https://example.com/api", {"status": "ok"})
```

`monitor_traffic()` captures a handful of packets while
`secure_communication()` sends an HTTPS POST request with basic error handling.

### Privacy considerations

Packet captures and session recordings can reveal private details about network
activity and spoken conversations. Always inform participants about what will be
logged and obtain explicit consent before starting a capture or recording. The
network utilities write PCAP files under `network_logs/` while audio clips are
stored in `logs/audio/`. Delete these files when they are no longer needed.
Use the `--output` or `--log-dir` options to redirect captures to a temporary
location or disable the calls to `session_logger.log_audio()` and
`session_logger.log_video()` if logging is unnecessary.


## Soul-Code Architecture

The spiritual core of INANNA is the **RFA7D** grid.  This seven‑dimensional
array of complex numbers acts as the "soul" and is hashed with SHA3‑256 to
produce an integrity signature.  The
[`GateOrchestrator`](docs/SOUL_CODE.md) exposes two methods that function as the
seven gates, mapping text into a 128‑element vector with `process_inward()` and
back to UTF‑8 with `process_outward()`.

## Example voice invocation

After deploying `soul_finetune.yaml` you can run the voice loop and observe how
the transcript passes through the gates.  The CLI prints the final reply along
with the core's integrity hash — the "soul signature":

```bash
python -m INANNA_AI.main --duration 3
python -m INANNA_AI.main --duration 3 --personality albedo
```

Example output:

```
Transcript: hello
Response: hi there gate [sig: 0123abcd...]
Voice path: resp.wav
```

When the listening engine detects extended quiet it calls
`silence_reflection.silence_meaning()` and stores the result under the
`"silence_meaning"` field. This hints at whether the pause was brief or a
longer moment of reflection.

### Avatar stream and sonic features

Start the orchestrator with `python start_spiral_os.py` and type
`appear to me` to begin streaming the avatar. Loading
`web_console/index.html` triggers the same command automatically so the
video appears in your browser. Generate a short song with
`play_ritual_music.py` and pass the resulting WAV file to
`stream_avatar_audio()` to synchronise mouth movement with the audio.

The sovereign voice milestone also lets you feed hexadecimal bytes into the
pipeline:

```bash
python INANNA_AI_AGENT/inanna_ai.py --hex 00ff
```

```python
from pathlib import Path
from core.avatar_expression_engine import stream_avatar_audio

for _ in stream_avatar_audio(Path("qnl_hex_song.wav")):
    pass
```

The audio workflow now threads each generated waveform through MFCC
analysis, pitch shifting and text‑to‑music generation.  These steps call
`vector_memory.add_vector` so the system can recall how a sound evolved.
At startup the listening engine performs an initial recording and stores
the detected emotion under `initial_listen`.

### Voice configuration and personality layers

Adjust pitch and speed for each archetype in `voice_config.yaml` or set
`VOICE_CONFIG_PATH` to point to a custom file. The file maps a persona name to
`pitch`, `speed` and a `tone` preset.

Voice avatars can be described in `voice_avatar_config.yaml`. Each entry sets
attributes like `timbre`, `gender`, `resonance` and the default `tone` preset.
Set `VOICE_AVATAR_CONFIG_PATH` if you want to load a different file.

```yaml
Baritone:
  timbre: warm
  gender: male
  resonance: low
  tone: calm
Soprano:
  timbre: bright
  gender: female
  resonance: high
  tone: excited
```

Activate Nigredo, Rubedo or Citrinitas via the CLI to modulate responses:

```bash
python -m INANNA_AI.main --personality nigredo_layer
python -m INANNA_AI.main --personality rubedo_layer
learning_mutator.py --activate citrinitas_layer
```

The selected layer and recent emotional analysis are stored in
`data/emotion_state.json` for review.

#### Layer configuration and glyph display

Optional personality layers can be toggled in `crown_config/settings/layers.yaml`.
Set a layer to `false` to disable it:

```yaml
layers:
  nigredo_layer: true
  rubedo_layer: false
```

When running `start_crown_console.py` or the web console, the current emotion
appears alongside a spiral glyph. Glyphs update automatically as new messages
are processed.
Example helper scripts under `scripts/` show the active configuration and the
last recorded emotion:

```bash
python scripts/list_layers.py
python scripts/show_emotion_glyph.py
```

### Voice Aura FX

`audio/voice_aura.py` selects a reverb and delay preset for the active emotion and
applies it with `sox` when available. If `sox` is missing the script falls back
to `pydub`.  Optional RAVE or NSynth checkpoints can further blend the timbre
via `dsp_engine.rave_morph` or `nsynth_interpolate`.

### Fetch Project Gutenberg texts

```bash
python -m INANNA_AI.main fetch-gutenberg "Frankenstein" --max 2
```

### Fetch GitHub repositories

```bash
python -m INANNA_AI.main fetch-github
```

You can also run the scraper module directly which reads repository names from
`learning_sources/github_repos.txt` and stores README files and commit logs
under `data/github`:

```bash
python -m INANNA_AI.learning.github_scraper
```

Set `GITHUB_TOKEN` in `secrets.env` to avoid API rate limits.

## Retrain the language model

Feedback from `training_guide.py` accumulates in `data/feedback.json`. When the
number of new intents reaches the `RETRAIN_THRESHOLD` value the helper script
`auto_retrain.py` can fine‑tune the local model:

```bash
python auto_retrain.py --run
```

This prints novelty and coherence scores and invokes the API when conditions are
met.

## Verify core integrity

At any point you may confirm that the RFA7D grid has not been tampered with:

```bash
python - <<'EOF'
from INANNA_AI.rfa_7d import RFA7D
core = RFA7D()
print('valid:', core.verify_integrity())
print('soul signature:', core.integrity_hash)
EOF
```

`verify_integrity()` recomputes the SHA3‑256 hash and compares it to the stored
value, ensuring the grid and its signature still match.

## Crown Agent Console

Launch the main GLM service and interactive console using the helper script
`crown_model_launcher.sh`. The script loads `secrets.env`, ensures the
GLM‑4.1V‑9B weights are present and starts a local API compatible with the
`GLMIntegration` class.

```bash
./crown_model_launcher.sh
```

Run `launch_servants.sh` to start additional models defined in
`secrets.env`. The script checks `DEEPSEEK_URL`, `MISTRAL_URL` and
`KIMI_K2_URL`; if any of them point to a localhost URL the respective model
is launched using Docker or `vllm`. You can run this script separately to
start the servant models without relaunching the main GLM service.

```bash
./launch_servants.sh
```

Use `start_crown_console.sh` to launch these services and automatically
open the interactive console once the endpoints are ready.

```bash
./start_crown_console.sh
```

Alternatively run the Python wrapper to load `secrets.env`, start the
console and streaming server, and wait for both processes:

```bash
python start_crown_console.py
```

After initialization the console displays the prompt:

```
crown>
```

Once the service is running you can start the REPL:

```bash
python console_interface.py
```

Pass `--speak` to synthesize each reply using the local voice engine:

```bash
python console_interface.py --speak
```

When speech mode is active each reply is saved as `resp.wav` and
immediately analyzed by `speech_loopback_reflector.py`. The detected
emotion is fed into `emotional_synaptic_engine.py` so subsequent answers
gradually adapt their tone.

Example session:

```
crown> hello
(voice plays)  # reflection adjusts future speed and pitch
```

The prompt `crown>` accepts natural language and `/exit` quits the session.

### Avatar Console

Run `start_avatar_console.sh` to launch the Crown services and begin streaming
the avatar alongside the console. The script calls
`start_crown_console.sh` in the background, starts `video_stream.py` and tails
`logs/INANNA_AI.log`. Set the optional `AVATAR_SCALE` environment variable to
adjust the video size.

See [docs/avatar_setup.md](docs/avatar_setup.md) for `.env` entries such as
`VIDEO_STREAM_URL` and `WEBRTC_TOKEN` that enable real-time streaming.

Type `appear to me` at the prompt to toggle the avatar stream. This command is
handled by :mod:`core.task_parser` and switches
`context_tracker.state.avatar_loaded` so the video engine begins emitting
frames. For guidance on customizing the avatar textures edit
`guides/avatar_config.toml` as described in
[`docs/avatar_pipeline.md`](docs/avatar_pipeline.md).

### Avatar Room

Open `web_console/game_dashboard/index.html` and complete the setup wizard to
reach the game dashboard. The **Avatar Room** panel streams the avatar via
WebRTC and provides quick controls:

- **Wave** – trigger a greeting gesture.
- **Speak** – enter a short phrase and press *Speak* to voice it.
- **Show Status** – request the avatar's current state.

A small chat field forwards operator questions to a sidekick helper which
searches the document registry for answers.

## HTTP Interface

`server.py` exposes a small FastAPI application with a `/glm-command` endpoint.
Start the server and invoke it with `curl`:

```bash
curl -X POST http://localhost:8000/glm-command \
     -H 'Content-Type: application/json' \
     -d '{"command": "ls"}'
```

The JSON response contains the GLM result under `result`.

### Telegram and Discord bots

Two helper scripts forward chat messages to the HTTP endpoint and reply with
text and synthesized audio:

```bash
python tools/bot_telegram.py  # requires TELEGRAM_BOT_TOKEN
python tools/bot_discord.py   # requires DISCORD_BOT_TOKEN
```

Both scripts read `WEB_CONSOLE_API_URL` to locate the `/glm-command` endpoint
and send voice replies generated by :mod:`core.expressive_output`.

## ZI.MU.TU.LU OS Guardian

The OS Guardian automates desktop actions while enforcing strict safety
policies. Install the project with the development extras and run the helper
container script:

```bash
pip install .[dev]
bash scripts/setup_os_guardian.sh
```

Once inside the container the ``os-guardian`` command exposes basic tools:

```bash
os-guardian open_app /usr/bin/gedit
os-guardian click 100 200
os-guardian plan "open the browser"
```

See [docs/os_guardian.md](docs/os_guardian.md) for an overview of the
perception, action, planning and safety modules.

## License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE)
for details.
