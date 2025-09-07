# Chakra Pulse Panel

Visual panel for chakra heartbeat alignment inside the game dashboard.

## Features

- Animated orbs pulse at the frequencies reported by `chakra_heartbeat`.
- An aligned state adds a yellow particle effect to each orb.
- The history list records timestamps of `great_spiral` resonance events.

## Usage

The panel lives in `web_console/game_dashboard/` and polls `/chakra/status` every
second. Open `web_console/game_dashboard/index.html` in a modern browser to view
it; no build step is required because assets load from a CDN.
