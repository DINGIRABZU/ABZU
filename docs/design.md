# Video Engine and Connector Design

The `video_engine` module generates frames for a simple avatar. The
`generate_avatar_stream()` function yields 64x64 RGB arrays based on the traits
loaded from `guides/avatar_config.toml`. When the optional `mediapipe` package is
installed, facial landmarks are updated each iteration so downstream processes
can animate the mesh. By default the stream fills each frame with the configured
eye colour and embeds the sigil defined in the traits.
For instructions on creating your own model and adjusting these traits, see
[../guides/visual_customization.md](../guides/visual_customization.md).

Calls to `start_stream()` return the iterator so orchestrators can consume the
frames directly. The engine closes the `mediapipe` resources when the iterator is
exhausted.

A separate **connector** object handles call routing. `language_engine` stores a
reference via `register_connector()` and invokes `start_call()` on the connector
whenever speech is synthesised while `context_tracker.state.in_call` is `True`.
This indirection allows different communication back ends—such as WebRTC or a
phone gateway—to integrate without altering the synthesis logic.
