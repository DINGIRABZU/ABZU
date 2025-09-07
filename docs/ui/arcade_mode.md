# Arcade Mode Widgets

The arcade console now surfaces minimal chakra telemetry.

## Widgets

- **Chakra Pulse Bar** – horizontal bars pulse at frequencies from `/chakra/status`.
- **Last Alignment Timestamp** – updates when all chakras report in sync.

## Relation to Game Dashboard

These widgets poll the same `/chakra/status` endpoint used by the [Game Dashboard](game_dashboard.md) but present a lightweight view without React.
