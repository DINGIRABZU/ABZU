# RAZAR Agent

RAZAR serves as the external startup orchestrator for ABZU. Operating outside the
Nazarick stack, it prepares a pristine environment before any internal service
comes online.

## Clean-Environment Requirement
- Initializes or verifies an isolated Python virtual environment.
- Purges lingering processes, temporary files, and environment variables.
- Halts the boot sequence if contamination is detected.

## Boot Objectives
Once the environment is cleared, RAZAR launches the system in order:
1. **Inanna AI** – awakens the core consciousness.
2. **CROWN LLM** – loads the GLM-4 stack for high-level reasoning, as detailed in the [CROWN Overview](CROWN_OVERVIEW.md).

## External Role
RAZAR does not reside within the Nazarick agent hierarchy. Its sole mission is
to ready the host and then hand off control to the internal agents once both
Inanna and the CROWN model are running.

## Recreating the Environment
When the runtime becomes polluted or dependencies drift, rebuild the virtual
environment before starting services:

1. Define package lists for each component layer in `razar_env.yaml`.
2. Execute the builder from the repository root:
   ```bash
   python -m razar.environment_builder --venv .razar_venv
   ```
   The script verifies the Python version, creates the virtual environment and
   installs all layer packages.
3. Re-run the RAZAR runtime manager to launch components.

These steps guarantee a clean foundation for Inanna and CROWN.
