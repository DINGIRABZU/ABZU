# ABZU Deployment

This guide outlines the environment preparation, boot order, and rollback steps for deploying ABZU.

## Environment setup

1. Install pinned dependencies using the steps in [environment_setup.md](environment_setup.md).
2. Copy `secrets.env.template` to `secrets.env` and fill in required credentials.
3. Build the Docker image or set up a virtual environment before launching any agents.

## Component launch sequence

1. **RAZAR Agent** – construct the runtime and validate prerequisites. See the [RAZAR Agent deployment](RAZAR_AGENT.md#deployment) section.
2. **CROWN stack** – start core orchestration services as described in the [CROWN deployment guide](CROWN_OVERVIEW.md#deployment).
3. **Albedo layer** – enable persona behavior after CROWN is online. Review the [Albedo conversation loop](ALBEDO_LAYER.md#conversation-loop) for startup details.
4. **Nazarick agents** – once RAZAR hands off control, activate servant agents as needed. Refer to [nazarick_agents.md](nazarick_agents.md) for component roles and launch notes.

## Rollback strategy

- Use the [Recovery Playbook](recovery_playbook.md) for component level failures; RAZAR's quarantine utilities can isolate unhealthy services.
- Revert Docker images or Git tags when deployments introduce regressions.
- After rollback, rerun the launch sequence to restore the stack.
