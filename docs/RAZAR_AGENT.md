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
