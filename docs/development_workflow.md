# Development Workflow

This page outlines the recommended steps for contributing to ABZU.

## Environment Setup

Create a virtual environment and install dependencies:

```bash
git clone https://github.com/your-org/ABZU.git
cd ABZU
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

See [setup.md](setup.md) for system packages and variables.

## Agent Cycle

Development centres on a planner–coder–reviewer loop. Launch the cycle with:

```bash
python start_dev_agents.py --objective "Refactor audio engine" --planner-model glm-4.1
```

`start_dev_agents.py` records the conversation to `data/interactions.jsonl` and logs events to `logs/dev_agent.log`.

## Testing

Run the test suite before committing changes:

```bash
pytest
```

For quick smoke tests of the command line interface:

```bash
bash scripts/smoke_console_interface.sh
```

Additional guidance is available in [testing.md](testing.md).

## Linting

Continuous integration runs [Ruff](https://docs.astral.sh/ruff/) and fails if any
lint errors are detected. Check your changes locally with:

```bash
ruff check .
```

Fix any reported issues before pushing to ensure the CI pipeline remains
green.

## Style and Contribution

Code follows the guidelines in [CODE_STYLE.md](../CODE_STYLE.md). Commits should
be small and include descriptive messages.

