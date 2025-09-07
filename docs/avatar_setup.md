# Avatar Setup

Configure the avatar pipeline by defining environment variables and adjusting textures.

## Environment variables

Add the following entries to your `.env` or `secrets.env` file:

```env
VIDEO_STREAM_URL="webrtc://localhost:9000/stream"
AVATAR_SCALE="1.0"
WEBRTC_TOKEN="change-me"
```

`VIDEO_STREAM_URL` points the client to the WebRTC or HTTP stream. `AVATAR_SCALE` adjusts the rendered frame size, and `WEBRTC_TOKEN` authenticates real-time sessions.

## Texture configuration

Customize avatar textures in `guides/avatar_config.toml`:

```toml
eye_color = [0, 128, 255]
sigil = "spiral"

[skins]
nigredo_layer = "skins/nigredo.png"
albedo_layer = "skins/albedo.png"
rubedo_layer = "skins/rubedo.png"
citrinitas_layer = "skins/citrinitas.png"
```

See [avatar_pipeline.md](avatar_pipeline.md) for the rendering workflow and optional package table.
