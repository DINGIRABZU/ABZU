# Nazarick Web Console

The Nazarick Web Console provides a browser-based interface for issuing commands, streaming the avatar, and testing music generation. It talks to the same FastAPI services used by agents and is intended for local development.

```mermaid
flowchart LR
    subgraph Browser
        I[index.html]
        M[main.js]
        O[operator.js]
    end
    M -->|commands| API[(FastAPI /glm-command)]
    M -->|WebRTC offer| WRTC[WebRTC Connector]
    O -->|uploadFiles| OP[Operator API]
    API -->|responses| M
    WRTC -->|media stream| M
```

## UI Components

- **`web_console/index.html`** – static page that loads the console and basic styles.
- **`web_console/main.js`** – handles command dispatch, emotion glyphs, music prompts, and WebRTC streaming.
- **`web_console/operator.js`** – helper module exposing `sendCommand`, `startStream`, and `uploadFiles` utilities for operator dashboards.

## Dependencies

- Modern browser with WebRTC, `fetch`, and MediaDevices APIs.
- Spiral OS backend providing the `/glm-command` and `/offer` endpoints.
- [WebRTC Connector](../connectors/webrtc_connector.py) and [Operator API](../operator_api.py) for streaming and file uploads. See the [Connector Index](connectors/CONNECTOR_INDEX.md) for a full list of modules.

## Launch Steps

1. Start the Spiral OS backend or run `scripts/start_local.sh` to launch containers.
2. Set `WEB_CONSOLE_API_URL` to point at the FastAPI server if different from the default `http://localhost:8000/glm-command`.
3. Serve the static files:
   ```bash
   cd web_console
   python -m http.server
   ```
4. Open `index.html` in a browser and grant microphone and camera access.
5. Enter commands or music prompts. Logs and streams display in real time.

