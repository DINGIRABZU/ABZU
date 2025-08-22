# Testing

## Manual smoke tests

### CLI console interface
1. From the repository root, run `python -m cli.console_interface`.
2. Confirm that an interactive prompt (e.g., `INANNA>`) appears and accepts input.
3. Exit with `Ctrl+C` when finished.

### Avatar console
1. Run `bash start_avatar_console.sh`.
   - Ensure `start_crown_console.sh` is executable or invoke it with `bash`.
2. Wait for WebRTC initialization messages in the logs and verify that a video feed is displayed.
3. Use `Ctrl+C` to terminate the services.

## Notes
- The CLI console repeatedly attempted to reach the GLM service at `http://localhost:8000/health` and never displayed a prompt before being interrupted.
- `start_avatar_console.sh` could not execute `start_crown_console.sh` (permission denied), so the WebRTC video feed did not initialize.
