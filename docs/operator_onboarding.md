# Operator Onboarding Wizard

The Game Dashboard includes a modal wizard that guides operators through essential setup tasks.

## Wizard Flow
1. **Avatar Config** – The wizard checks for `avatar_config.toml`. If not found, it prompts the operator to place the file on the server.
2. **API Tokens** – Verifies required API tokens via the `/token-status` endpoint. Missing tokens trigger a reminder to update `secrets.env`.
3. **Completion** – When both checks pass, the wizard records completion in `localStorage` and unlocks the dashboard.

## Progress Persistence
Current step and completion state are stored in `localStorage` so operators can resume the wizard after closing the browser.

## Multi-Agent Streams
1. Launch the servant processes with `start_dev_agents.py` or via the dashboard's **Agents** panel.
2. When prompted, select the agents to stream and confirm the WebRTC session for each.
3. Use the **Streams** tab to verify audio and video for every agent.

## Monitor Chakra Pulses
1. Open the **Chakra Monitor** from the dashboard sidebar.
2. Confirm each layer emits pulses at the expected 1 : 1 ratio.
3. Pulses that drop or drift trigger alerts; follow the [Recovery Playbook](recovery_playbook.md) to restore alignment.

## Related Documents
- [README_OPERATOR.md](../README_OPERATOR.md)
