# 3D Avatar API

The 3D Avatar API streams animated meshes to viewers and exposes
configuration hooks for the avatar pipeline. Crown routes operator
commands to the service which renders frames and synchronises audio.

## Streaming Flow

```mermaid
flowchart LR
    Operator --> Crown --> "3D Avatar Service" --> Viewer
```

## Configuration

The service reads mesh paths, camera paths, and optional lip‑sync audio
from `avatar_config.toml`. Set `mode = "3d"` under `[avatars]` to enable
three‑dimensional rendering. Crown forwards the configuration on
startup and when operators adjust avatar options.

## Dependencies

The API activates additional packages when present:

| Package      | Purpose |
|--------------|---------|
| `aiortc`     | Provides WebRTC transport for real‑time streaming |
| `ffmpeg`     | Encodes and muxes avatar video output |
| `SadTalker`  | Drives facial animation directly from speech samples |
| `Wav2Lip`    | Supplies high‑quality lip‑sync fallback |
| `ControlNet` | Enables gesture modulation via diffusion guides |
| `AnimateDiff`| Generates motion sequences for gestures |

Missing packages simply disable their corresponding features while the
service continues with basic rendering.

## Version History

- 2025-10-24: Initial draft.
