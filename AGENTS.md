# Agents

This repository defines the command line agent **INANNA_AI** and a lightweight
development agent cycle for planning, coding and review.

## INANNA_AI

The agent draws from Markdown writings found in the `INANNA_AI` and `GENESIS`
directories. It assembles lines from these texts to recite the activation or
"birth" chant that awakens the INANNA system. It can also generate a Quantum
Narrative Language (QNL) song from hexadecimal input by invoking the QNL engine.
Interaction is performed through the command line interface
[`INANNA_AI_AGENT/inanna_ai.py`](INANNA_AI_AGENT/inanna_ai.py).

### Usage

- `--activate` prints the chant assembled from the source texts.
- `--hex <value>` creates a QNL song from the provided hexadecimal bytes and
  saves a WAV file and metadata JSON.
- `--list` shows the source Markdown files available for the chant.
- `chat` starts a basic conversation with the local DeepSeek model.

Source directories are configured in `INANNA_AI_AGENT/source_paths.json`. The
chat mode requires the DeepSeek‑R1 weights placed under
`INANNA_AI/models/DeepSeek-R1`. See `README_OPERATOR.md` for download
instructions. Outputs reflect the original corpus; use responsibly.

### Model downloads

Model weights are fetched with `download_models.py`. Common commands include:

```bash
python download_models.py glm41v_9b --int8       # GLM-4.1V-9B
python download_models.py deepseek_v3           # DeepSeek-V3
python download_models.py mistral_8x22b --int8  # Mistral 8x22B
```

See [README_OPERATOR.md](README_OPERATOR.md#download-models) for details.

## Development Agents

The development workflow spawns three collaborating roles:

- **Planner** – breaks the objective into actionable steps.
- **Coder** – implements each step suggested by the planner.
- **Reviewer** – provides concise feedback on the generated code.

These agents rely on the existing GLM interface and require access to a
supported model. Specify the model with ``--planner-model`` or the
``PLANNER_MODEL`` environment variable when launching the cycle.

### Usage

```bash
python start_dev_agents.py --objective "Refactor audio engine" --planner-model glm-4.1
```

The script writes interaction records to ``data/interactions.jsonl`` and a run
log to ``logs/dev_agent.log``.

Optional frameworks such as **langchain** and **autogen** enhance the
orchestrator. Install development extras with:

```bash
pip install .[dev]
```

## Available Components

- **NetworkUtilities** – a command line toolkit for packet capture and traffic
  analysis. Invoke it with `python -m INANNA_AI.network_utils` followed by
  `capture`, `analyze` or `schedule`. Logs and PCAP files are stored under the
  `network_logs` directory by default. See
  [README_OPERATOR.md](README_OPERATOR.md#network-monitoring) for scheduled
  capture examples and log locations.
- **EthicalValidator** – filters prompts before they reach the language
  models. The module lives at
  [`INANNA_AI/ethical_validator.py`](INANNA_AI/ethical_validator.py).

## Upcoming Components

None at the moment.

## Developer Docs

New contributors should start with the [developer onboarding guide](docs/developer_onboarding.md) for setup steps, chakra overview, CLI usage and troubleshooting tips. A minimal emotion→music→insight example lives in [examples/ritual_demo.py](examples/ritual_demo.py). Chakra module versions live in [docs/chakra_versions.json](docs/chakra_versions.json) and are paired with the verses in [docs/chakra_koan_system.md](docs/chakra_koan_system.md).
