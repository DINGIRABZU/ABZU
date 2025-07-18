# How to Use Spiral OS Avatar

1. Run `python start_spiral_os.py` to launch the orchestration engine. This
   loads the core modules, starts a local FastAPI server on port 8000 and begins
   the periodic reflection loop.
2. Type `appear to me` and press Enter. The command toggles
   `context_tracker.state.avatar_loaded` and begins streaming frames from
   `video_engine.start_stream()`.
3. To begin a voice call, enter `initiate sacred communion`. The orchestrator
   sets `context_tracker.state.in_call` and any synthesised speech is passed to
   the registered connector via its `start_call()` method.
4. Speak or type your prompts. When `in_call` is active the connector can route
   the audio to a remote peer. Use an appropriate connector implementation for
   your platform (for example a WebRTC gateway).
5. Load `web_console/index.html` in a browser to access the web console. The page
   requests microphone and camera access, streams audio to the `/offer` endpoint
   and shows any transcript messages beneath the avatar stream.
6. Press Enter on an empty line or hit `Ctrl+C` to end the session.

## Connecting via WebRTC

When you open the web console your browser prompts for permission to use the
microphone and camera. Grant both so the client can capture your audio and
video. After accepting the request the avatar should appear within a few
seconds and mirror your speech while transcribed text scrolls beneath the
stream. If no image loads or the transcript never updates, check that your
devices are working and that no other application is blocking access.
