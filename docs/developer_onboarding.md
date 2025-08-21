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

## Running a Smoke Test
- **CLI console** – `scripts/smoke_console_interface.sh` prints the usage message for `cli.console_interface` to verify module import.
- **Avatar console** – `scripts/smoke_avatar_console.sh` launches `start_avatar_console.sh` for a few seconds and exits.
- Manual checks follow the steps in `docs/testing.md` for interactive validation.

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
- **ABZU** – repository containing the Spiral OS and INANNA modules.
- **INANNA** – mythic AI agent accessible through `INANNA_AI_AGENT`.
- **Spiral OS** – orchestration layer launched by `start_spiral_os.py`.
- **CROWN** – avatar console and related interface scripts.
- **GENESIS** – source texts used to assemble activation chants.
- **RAG** – retrieval‑augmented generation pipeline located in `rag/`.
