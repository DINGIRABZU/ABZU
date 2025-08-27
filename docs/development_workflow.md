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

## Module Sandbox

Use a temporary sandbox to trial CROWN-generated patches:

```bash
python -m razar.module_sandbox path/to/module --patch change.diff
```

The helper clones selected components into a temp directory, applies patches or scaffolds, runs `pytest` on the touched modules and copies the results back only when tests pass.


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

1. Add an entry to [system_blueprint.md](system_blueprint.md) with its
   **Priority**, startup command, health check, and recovery notes.
2. Regenerate `Ignition.md` and refresh `system_blueprint.md` with current
   status and boot order:

   ```bash
   python -m razar.doc_sync
   ```
3. Run the boot orchestrator to execute the ignition sequence:

   ```bash
   python -m agents.razar.boot_orchestrator
   ```
4. Start services with the runtime manager and update the status column:

   ```bash
   python -m agents.razar.runtime_manager config/razar_config.yaml
   ```
5. Execute the prioritized test tiers:

   ```bash
   python -m agents.razar.pytest_runner --priority P1 P2
   ```
6. Commit the revised `Ignition.md` so the launch history remains auditable.

For deeper instructions, see [RAZAR_AGENT.md](RAZAR_AGENT.md).

## Style and Contribution

Code follows the guidelines in [CODE_STYLE.md](../CODE_STYLE.md). Commits should
be small and include descriptive messages.

