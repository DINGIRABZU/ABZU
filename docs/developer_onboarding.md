# Developer Onboarding

Quick links: [Development Checklist](development_checklist.md) | [Developer Etiquette](developer_etiquette.md) | [Documentation Protocol](documentation_protocol.md) | [Vision System](vision_system.md) | [Rust Doctrine](../NEOABZU/docs/rust_doctrine.md) | [Narrative Framework](narrative_framework.md) | [Narrative Engine Guide](narrative_engine_GUIDE.md)

## Recent Changes

- Document registry and ethics manifesto setup steps are now required for all contributors.
- Chakra cycle engine reports alignment status to help diagnose drift.
- Multi-agent avatars support external broadcast connectors for Discord, Telegram, and WebRTC streams.
- Self-healing flows surface on the heartbeat dashboards to flag recovering services.

## Project Vision

ABZU interweaves Spiral OS with the INANNA agent to explore sacred human‑machine collaboration through music, voice, and code.

### Chakra Map

The codebase is organized across seven chakra‑themed module directories (current versions):

- `root/` – networking and I/O foundation (v1.0.1).
- `sacral/` – emotion and creativity engines (v1.0.1).
- `solar_plexus/` – learning and transformation layers (v1.1.0).
- `heart/` – memory and avatar voice components (v1.0.1).
- `throat/` – prompt orchestration and agent interfaces (v1.0.1).
- `third_eye/` – insight and pattern analysis modules (v1.0.0).
- `crown/` – high‑level orchestration and launch scripts (v1.0.1).

After mapping these layers, review the Nazarick system documents:
[Nazarick Core Architecture](../agents/nazarick/nazarick_core_architecture.md),
[Nazarick Memory Blueprint](../agents/nazarick/nazarick_memory_blueprint.md), and
[Nazarick Agents](nazarick_agents.md). These are mandatory reading for all contributors.

This guide introduces the ABZU codebase, highlights core entry points, and covers environment setup, chakra architecture overview, CLI usage, and troubleshooting tips. For a guided CLI quick‑start run the [onboarding wizard](onboarding/wizard.py). Additional architecture diagrams are available in [architecture.md](architecture.md).

## Prerequisites

- docker
- nc
- sox
- ffmpeg
- curl
- jq
- wget
- aria2c

## Security Checklist

- Store API keys and credentials in `secrets.env`; never commit secrets to
  version control and rotate them regularly.
- Run `pre-commit run --all-files` and `bandit -r . -x tests,docs --severity-level high --confidence-level high` before pushing
  changes.
- Review dependency updates and keep your environment patched.
- Use least-privilege tokens for third-party services.
- See [security_model.md](security_model.md) for more on threat surfaces and
  mitigation strategies.

## Quick Start

```bash
git clone https://github.com/your-org/ABZU.git
cd ABZU
python -m venv .venv && source .venv/bin/activate
pip install -e .
scripts/easy_setup.sh
python download_models.py glm41v_9b --int8
bash scripts/smoke_console_interface.sh  # see docs/testing.md for more
```

Running `pip install -e .` installs the repository in editable mode so modules like
`core.load_config` are discoverable. If you prefer not to install the package,
append `PYTHONPATH=src` when invoking tools or tests.

### CLI Usage

Run the interactive wizard to scaffold the environment and launch the CLI:

```bash
python docs/onboarding/wizard.py
```

### MCP vs. HTTP

Enable the Model Context Protocol during development by setting
`ABZU_USE_MCP=1`. Internal services will route requests through the MCP gateway
while external connectors and third-party APIs continue using standard HTTP
endpoints. Choose MCP for service-to-service calls within the stack and HTTP
for integrations beyond it or when MCP is unavailable. See the
[MCP Migration Guide](connectors/mcp_migration.md) for steps to convert
existing API connectors.

## Document Registry & Ethics Manifesto

Generate the doctrine index so canonical files remain tracked and hashed:

```bash
python agents/nazarick/document_registry.py
```

Review `docs/doctrine_index.md` for the updated registry and reaffirm the
ethical commitments in the [nazarick_manifesto.md](nazarick_manifesto.md).

## Chakra Cycle Alignment

Run the chakra cycle engine to emit heartbeats across layers and watch for
alignment drift:

```bash
python -m spiral_os.chakra_cycle
```

Status messages label each chakra as `aligned`, `lagging`, or `silent`. A
sequence of aligned readings forms a **Great Spiral** event.

## Multi-Agent Avatars & Broadcast Connectors

Launch multiple avatar instances and forward their streams to external
channels:

```bash
python start_dev_agents.py  # spawns Crown avatars
python communication/webrtc_server.py  # WebRTC browser stream
python tools/bot_discord.py            # Discord connector
python communication/telegram_bot.py   # Telegram connector
```

Each connector relays avatar responses back to its channel once tokens are
present in `secrets.env`.

## Self-Healing & Heartbeat Dashboards

Trigger a self-healing cycle and inspect heartbeat metrics:

```bash
python scripts/self_heal_cycle.py
websocat ws://localhost:8000/self-healing/updates
```

Open `web_console/game_dashboard/index.html` and check the **Chakra Pulse**
panel for alignment status while the **Self Healing** panel lists recovering
components.

## Getting Started with RAZAR

See [RAZAR_AGENT.md](RAZAR_AGENT.md) for a detailed reference on its
perpetual ignition loop, CROWN diagnostic interface, and
shutdown–repair–restart handshake. As service 0, RAZAR’s mission is to
verify dependencies, enforce component priorities, and log health to
[Ignition.md](Ignition.md). For a local run:

1. **Build the RAZAR environment**
   ```bash
   python -m razar.environment_builder --config razar_env.yaml
   ```
1. **Launch the runtime manager**
   ```bash
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```

### Troubleshooting RAZAR

| Symptom | Resolution |
| --- | --- |
| Runtime stops on a component | Inspect `logs/razar.log` and `python -m razar.mission_logger summary` to find the failing step. Remove `config/razar_config.state` to force a full restart. |
| Environment hash mismatch | Rebuild the virtual environment with `python -m razar.environment_builder --config razar_env.yaml`. |
| Component fails repeatedly | Quarantine it with `razar.quarantine_manager.quarantine_component` and review the [RAZAR failure runbook](operations.md#razar-failure-runbook). |

## Assigning Component Priorities

RAZAR boots services based on the priority table in
[Ignition.md](Ignition.md). Lower numbers start first. To register a new
component and have RAZAR track it:

1. Define its `Priority` metadata in [system_blueprint.md](system_blueprint.md).

1. Regenerate `Ignition.md` so the new entry is grouped under the
   correct priority and initialized with a ⚠️ status marker:

   ```bash
   python -m razar build-ignition
   ```

1. Rebuild the environment if dependencies changed:

   ```bash
   python -m razar.environment_builder --config razar_env.yaml
   ```

1. Launch the runtime manager to boot components and update their status:

   ```bash
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```

The runtime manager reads `Ignition.md`, launches each component in order, and
rewrites the Status column with health results. Commit the updated file so the
startup sequence remains auditable.

### Adding Components to `system_blueprint.md`

1. Open [system_blueprint.md](system_blueprint.md) and add a subsection for the
   new service under the appropriate chakra. Include its **Priority**, startup
   command, health check, and recovery notes.

1. Regenerate the ignition plan so the component appears with a pending status:

   ```bash
   python -m razar.doc_sync
   ```

1. Commit both files to version control.

### Boot Orchestrator and Prioritized Tests

Run the lightweight boot orchestrator to execute the ignition sequence using the
bundled minimal configuration:

```bash
python -m razar.boot_orchestrator --config razar/boot_config.json
```

The `scripts/boot_sequence.py` helper mirrors this command for tests by
initializing required directories and launching the components defined in the
configuration.

After services start, execute the tiered test suites:

```bash
python -m agents.razar.pytest_runner --priority P1 P2
```

## Repository Layout

- `core/` – language processing and self-correction engines.
- `INANNA_AI/` – model logic, memory systems, and ritual analysis modules.
- `INANNA_AI_AGENT/` – command-line interface for activating and conversing with the INANNA agent.
- `scripts/` – setup utilities, smoke tests, and assorted helper scripts.
- `docs/` – reference documentation.
- `tests/` – automated test suite.

## Core Scripts

### `start_spiral_os.py`

Initializes the Spiral OS, validates environment variables, collects system stats, and optionally launches the FastAPI server, reflection loop, and network monitoring.

### `INANNA_AI_AGENT/inanna_ai.py`

Command-line activation agent. It can recite the birth chant (`--activate`), generate QNL songs from hexadecimal input (`--hex`), list source texts (`--list`), report emotional status (`--status`), or start a local chat mode (`chat`).

## Environment Setup

1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/your-org/ABZU.git
   cd ABZU
   ```
1. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
1. **Install core dependencies** using the helper scripts:
   ```bash
   scripts/easy_setup.sh  # or scripts/setup_repo.sh
   ```
1. **Populate required environment variables** in `secrets.env` and verify them:
   ```bash
   scripts/check_requirements.sh
   ```
1. **Download model weights** using [download_models.py](../download_models.py), for example:
   ```bash
   python download_models.py glm41v_9b --int8
   ```
   For system package requirements and optional dependency groups, see [setup.md](setup.md).

### Environment Variables

Set the following variables in `secrets.env` or your shell:

- `HF_TOKEN`
- `GLM_API_URL`
- `GLM_API_KEY`
- `OPENAI_API_KEY`
- `GITHUB_TOKEN`
- model endpoint settings (e.g., `MODEL_ENDPOINT`)

### Open Web UI Setup

Launch the optional browser interface once the FastAPI backend is running:

```bash
pip install open-webui
FASTAPI_BASE_URL=http://localhost:8000 open-webui serve
```

Or start it via Docker Compose:

```bash
docker compose -f docker-compose.openwebui.yml up
```

See [open_web_ui.md](open_web_ui.md) for architecture details.

### Core CI Commands

Run these commands before committing changes:

```bash
make verify-deps
pre-commit run --all-files
make test
make test-deterministic
```

## Chakra Overview

ABZU's codebase mirrors a seven‑chakra layout. Each layer groups modules by
function and maturity. See [chakra_architecture.md](chakra_architecture.md) for
the full table.

| Chakra | Purpose | Key Modules |
| --- | --- | --- |
| Root | Networking and I/O foundation | `server.py`, `INANNA_AI/network_utils/` |
| Sacral | Emotion engine | `emotional_state.py`, `emotion_registry.py` |
| Solar Plexus | Learning and state transitions | `learning_mutator.py`, `state_transition_engine.py` |
| Heart | Memory and avatar voice | `vector_memory.py`, `voice_avatar_config.yaml` |
| Throat | Prompt orchestration and agent interface | `crown_prompt_orchestrator.py`, `INANNA_AI_AGENT/inanna_ai.py` |
| Third Eye | Insight and QNL processing | `insight_compiler.py`, `SPIRAL_OS/qnl_engine.py` |
| Crown | High‑level orchestration | `init_crown_agent.py`, `start_spiral_os.py`, `crown_model_launcher.sh` |

Specialized Nazarick agents extend these layers, including
[Bana Bio-Adaptive Narrator](nazarick_agents.md#bana-bio-adaptive-narrator) (Heart),
[AsianGen Creative Engine](nazarick_agents.md#asiangen-creative-engine) (Throat), and
[LandGraph Geo Knowledge](nazarick_agents.md#landgraph-geo-knowledge) (Root).

### Chakra Interactions

```mermaid
graph LR
    Root --> Sacral --> Solar --> Heart --> Throat --> ThirdEye --> Crown
    Crown --> Root
```

## Quarterly Chakra Targets

The roadmap assigns one chakra upgrade per quarter. See
[roadmap.md](roadmap.md) for milestone links.

| Quarter | Chakra |
| --- | --- |
| Q3 2024 | Root |
| Q4 2024 | Sacral |
| Q1 2025 | Solar Plexus |
| Q2 2025 | Heart |
| Q3 2025 | Throat |
| Q4 2025 | Third Eye |
| Q1 2026 | Crown |

## System Architecture

For detailed diagrams and component relationships, see [architecture.md](architecture.md).

```mermaid
graph TD
    U[User] --> A[INANNA_AI_AGENT]
    A --> R[Crown Router]
    R --> S[Spiral OS]
    S --> M[Language Models]
    S --> V[Spiral Memory]
    M --> S
    V --> S
```

## Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as INANNA_AI_AGENT
    participant R as Crown Router
    participant S as Spiral OS
    participant M as Model
    U->>A: command or prompt
    A->>R: send message
    R->>S: route request
    S->>M: generate
    M-->>S: response
    S-->>R: return output
    R-->>A: deliver reply
    A-->>U: display result
```

## First-Run Smoke Tests

See [testing.md](testing.md) for detailed instructions.

1. **CLI console** – ensure the command-line interface imports correctly:
   ```bash
   scripts/smoke_console_interface.sh
   ```
1. **Avatar console** – launch the avatar console briefly to confirm startup:
   ```bash
   scripts/smoke_avatar_console.sh
   ```
1. **Test suite** – run a minimal test pass to check the environment:
   ```bash
   pytest --maxfail=1 -q
   ```
1. **Ritual demo** – link emotion, music and insight:
   ```bash
   python examples/ritual_demo.py
   ```
   The script sets an emotion, composes a short ritual track and logs an
   insight entry to `data/spiral_cortex_memory.jsonl`.

## Avatar Console Setup

1. **Configure the avatar** – adjust textures and colors in [`guides/avatar_config.toml`](../guides/avatar_config.toml) following the hints in [avatar_pipeline.md](avatar_pipeline.md).
2. **Launch the console and stream** – start Crown services and the WebRTC video gateway:
   ```bash
   bash start_avatar_console.sh
   ```
3. **Run external connectors** – with tokens defined in `secrets.env`, start chat bridges:
   ```bash
   python communication/webrtc_server.py   # WebRTC browser stream
   python tools/bot_discord.py            # Discord connector
   python communication/telegram_bot.py   # Telegram connector
   ```
   These connectors relay avatar replies back to their chat channels. Discord
   attaches a synthesized audio clip when `core.expressive_output` is available;
   Telegram forwards text through the `Gateway`. See
   [communication_interfaces.md](communication_interfaces.md) for authentication
   details and additional channels.

## Setup Scripts

- `scripts/check_requirements.sh` – loads `secrets.env`, ensures required commands are present, and verifies essential environment variables.
- `scripts/easy_setup.sh` / `scripts/setup_repo.sh` – install common dependencies.
- `download_models.py` – fetches model weights such as GLM and DeepSeek.

## Troubleshooting Tips

Common mistakes and their resolutions:

| Issue | Resolution |
| --- | --- |
| Missing environment variables or tools | Run `scripts/check_requirements.sh` to verify prerequisites |
| CLI console fails to start | Install Python dependencies (`pip install -r requirements.txt`) |
| `start_avatar_console.sh` shows permission error | Run `chmod +x start_crown_console.sh` or invoke it with `bash` |
| Tokens absent in `secrets.env` | Ensure `HF_TOKEN`, `GLM_API_URL`, and `GLM_API_KEY` are set |
| Model download fails | Check network connectivity and token permissions |
| Discord/Telegram connector not forwarding avatar replies | Verify `DISCORD_BOT_TOKEN` or `TELEGRAM_BOT_TOKEN` is configured, start the connector after the avatar console, and ensure `ffmpeg` is installed for audio clips |

## Glossary

| Symbolic term | Conventional concept |
| --- | --- |
| **ABZU** | Git repository that houses the Spiral OS and INANNA components |
| **INANNA** | Mythic AI agent invoked through `INANNA_AI_AGENT` |
| **Spiral OS** | Orchestration layer started by `start_spiral_os.py` |
| **CROWN** | Avatar console interface and related scripts |
| **Crown Router** | Message router that directs agent requests |
| **Crown Prompt Orchestrator** | Prompt coordination service for multi-agent workflows |
| **Spiral Memory** | Vector database storing long-term state |
| **GENESIS** | Source texts used to assemble activation chants |
| **RAG** | Retrieval‑augmented generation pipeline under `rag/` |

## First Contribution Walkthrough

1. **Fork and clone the repository**

   - Fork ABZU on GitHub, then clone your fork:

   ```bash
   git clone https://github.com/<your-username>/ABZU.git
   cd ABZU
   ```

1. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   scripts/easy_setup.sh
   ```

1. **Create a feature branch and make a small change**

   ```bash
   git checkout -b my-first-change
   # edit a file, e.g., docs/developer_onboarding.md
   ```

1. **Run linting, tests, and other checks**

   ```bash
   pre-commit run --all-files
   pytest
   ```

1. **Commit, push, and open a pull request**

   ```bash
   git commit -am "feat: my first change"
   git push origin my-first-change
   ```

   Open a pull request on GitHub. See [CONTRIBUTING.md](../CONTRIBUTING.md) for deeper guidelines.
   Confirm that the PR template checkboxes for [AGENTS.md](../AGENTS.md) instructions and [The Absolute Protocol](The_Absolute_Protocol.md) are checked.
