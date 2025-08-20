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
- During this test run, the CLI setup encountered dependency initialization issues, preventing the prompt from appearing.
- `start_avatar_console.sh` reported a permission error for `start_crown_console.sh` and the WebRTC video stream did not start.
