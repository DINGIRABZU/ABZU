# Open Web UI Integration Guide

This guide describes how the Open Web UI front end connects to the ABZU server, the dependencies required, and the event flow for executing commands.

## Architecture

Open Web UI provides a multi-user chat interface that runs alongside the ABZU FastAPI application. Users interact with the Open Web UI in a browser, which issues HTTPS requests to the FastAPI backend. Command execution is handled by the `/glm-command` endpoint defined in [`server.py`](../server.py).

```
Browser ── Open Web UI ──> `/glm-command` ──> GLM shell
```

The Open Web UI layer does not maintain its own model runtime; it forwards commands to the existing backend and displays the returned output.

## Dependencies

- **Node.js** for serving the Open Web UI assets.
- **Python 3.11+** and the existing FastAPI stack running `server.py`.
- **GLM shell utilities** already bundled in this repository.
- Optional: a persistent database if Open Web UI session storage is required.

## Event Flow

1. A user enters a command in the Open Web UI chat box.
2. Open Web UI sends an authenticated `POST` request to `/glm-command`.
3. `server.py` validates the token and checks the command prefix.
4. The command is executed via `glm_shell.send_command` and the output is returned.
5. Open Web UI renders the result in the browser.

This flow centralizes command execution in the backend, reusing authorization and logging logic already present in `server.py`.

