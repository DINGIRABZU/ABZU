# Developer Onboarding

This guide introduces the ABZU codebase, highlights core entry points, and outlines basic verification steps.

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

## Step-by-Step Setup
1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/your-org/ABZU.git
   cd ABZU
   ```
2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install core dependencies** using the helper scripts:
   ```bash
   scripts/easy_setup.sh  # or scripts/setup_repo.sh
   ```
4. **Populate required environment variables** in `secrets.env` and verify them:
   ```bash
   scripts/check_requirements.sh
   ```
5. **Download model weights** as needed, for example:
   ```bash
   python download_models.py glm41v_9b --int8
   ```

## First-Run Smoke Tests
1. **CLI console** – ensure the command-line interface imports correctly:
   ```bash
   scripts/smoke_console_interface.sh
   ```
2. **Avatar console** – launch the avatar console briefly to confirm startup:
   ```bash
   scripts/smoke_avatar_console.sh
   ```
3. **Test suite** – run a minimal test pass to check the environment:
   ```bash
   pytest --maxfail=1 -q
   ```

## Setup Scripts
- `scripts/check_requirements.sh` – loads `secrets.env`, ensures required commands are present, and verifies essential environment variables.
- `scripts/easy_setup.sh` / `scripts/setup_repo.sh` – install common dependencies.
- `download_models.py` – fetches model weights such as GLM and DeepSeek.

## Troubleshooting
- Run `scripts/check_requirements.sh` to confirm environment variables and external tools.
- If the CLI console fails to start, ensure Python dependencies are installed (`pip install -r requirements.txt`).
- `start_avatar_console.sh` may need execution permission; run `chmod +x start_crown_console.sh` or invoke it with `bash` if permission errors appear.
- Verify `secrets.env` contains `HF_TOKEN`, `GLM_API_URL`, and `GLM_API_KEY`.

## Glossary
| Symbolic term | Conventional concept |
| --- | --- |
| **ABZU** | Git repository that houses the Spiral OS and INANNA components |
| **INANNA** | Mythic AI agent invoked through `INANNA_AI_AGENT` |
| **Spiral OS** | Orchestration layer started by `start_spiral_os.py` |
| **CROWN** | Avatar console interface and related scripts |
| **GENESIS** | Source texts used to assemble activation chants |
| **RAG** | Retrieval‑augmented generation pipeline under `rag/` |
