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

## Continuous Integration

Pull requests trigger the workflow defined in
`.github/workflows/ci.yml`. It runs `pre-commit` and the full pytest suite
to keep the codebase healthy. Model downloads are cached between runs so
tests execute quickly without repeatedly fetching weights.

To reproduce the checks locally before pushing changes:

```bash
pre-commit run --all-files
pytest
```

## Ignition Chain

RAZAR acts as service 0 and reads `Ignition.md` to determine boot order. The
file’s status markers (✅/⚠️/❌) reflect component health. See [Assigning
Component Priorities](developer_onboarding.md#assigning-component-priorities)
for a walkthrough. When introducing or modifying a service:

1. Set its **Priority** metadata in [system_blueprint.md](system_blueprint.md).
2. Regenerate `Ignition.md` from the blueprint so RAZAR picks up the new entry:

   ```bash
   python -m razar build-ignition
   ```
3. Run the runtime manager to start services and update the status column:

   ```bash
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```
4. Commit the revised `Ignition.md` so the launch history remains auditable.

For deeper instructions, see [RAZAR_AGENT.md](RAZAR_AGENT.md).

## Style and Contribution

Code follows the guidelines in [CODE_STYLE.md](../CODE_STYLE.md). Commits should
be small and include descriptive messages.

