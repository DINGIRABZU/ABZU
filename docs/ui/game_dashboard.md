# Game Dashboard

The game dashboard is a React single-page application that presents the avatar video feed alongside live chakra telemetry.

## Launch

1. Ensure the Spiral OS backend is running and reachable.
2. Open `web_console/game_dashboard/index.html` in a modern browser. React assets load from a CDN; no build step is required.
3. The page automatically connects to the avatar stream and event feed.

## Mission Map

The landing view renders a mission map with oversized controller-friendly buttons for common actions:

- **Ignite** – boot the system.
- **Memory Query** – request a memory scan.
- **Handover** – transfer control to the agent.

Use arrow keys or a gamepad's D‑pad to move focus. Activate a button with **Enter**, **Space**, or the gamepad **A** button.

## Telemetry

An event log under the video lists chakra metrics received from the server. Operators can watch the stream and metrics without touching code.
