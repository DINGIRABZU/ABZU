# Operator Onboarding Wizard

The Game Dashboard includes a modal wizard that guides operators through essential setup tasks.

## Wizard Flow
1. **Avatar Config** – The wizard checks for `avatar_config.toml`. If not found, it prompts the operator to place the file on the server.
2. **API Tokens** – Verifies required API tokens via the `/token-status` endpoint. Missing tokens trigger a reminder to update `secrets.env`.
3. **Completion** – When both checks pass, the wizard records completion in `localStorage` and unlocks the dashboard.

## Progress Persistence
Current step and completion state are stored in `localStorage` so operators can resume the wizard after closing the browser.

## Related Documents
- [README_OPERATOR.md](../README_OPERATOR.md)
