# Avatar Pipeline

The avatar pipeline synchronises generated speech with visual animation. It reads
configuration from `guides/avatar_config.toml` and produces frames via
`core.video_engine`.

## Heartbeat and Session Management

The video engine listens for the system heartbeat so avatar streams stay in sync
with the chakra cycle. Each active stream is tied to an operator session and is
renewed on every beat. If the heartbeat goes missing, the stream is marked
stalled and the pipeline triggers its self-healing routine to reconnect WebRTC
channels and reload textures before resuming playback. Session identifiers are
persisted in memory so multi-agent streams can restart without losing their
place in the narrative.

## Setup

Install the Python requirements and optional packages for lip sync:

```bash
pip install -r SPIRAL_OS/requirements.txt
```

Optional packages unlock richer animation and streaming features:

| Package    | Feature unlocked |
|------------|-----------------|
| `SadTalker` | Drives facial animation directly from the speech sample |
| `Wav2Lip`  | Adds high-quality lip sync fallback |
| `ControlNet` | Enables gesture modulation via diffusion guides |
| `AnimateDiff` | Generates motion sequences for gestures |
| `aiortc`   | Provides WebRTC transport for real-time streaming |
| `ffmpeg`   | Encodes and muxes avatar video output |

When **SadTalker** is available the video engine generates frames directly from
the speech sample. If not installed it falls back to **Wav2Lip** when present or
to a minimal mouth overlay.

Gesture control is supported through **ControlNet** or **AnimateDiff** if those
modules can be imported. The video engine calls `apply_gesture()` from the first
backend found to modify each frame.

`avatar_config.toml` now accepts a `[skins]` table that maps personality layer
names to avatar textures. Example:

```toml
eye_color = [0, 128, 255]
sigil = "spiral"

[skins]
nigredo_layer = "skins/nigredo.png"
albedo_layer = "skins/albedo.png"
rubedo_layer = "skins/rubedo.png"
citrinitas_layer = "skins/citrinitas.png"
```

Use the pipeline as follows:

```python
from pathlib import Path
from core.avatar_expression_engine import stream_avatar_audio

for frame in stream_avatar_audio(Path("chant.wav")):
    pass  # render or encode the frame
```

The repository previously included a small `sample_voice.wav` clip for quick
tests. To keep the documentation lightweight the binary asset was removed. You
can synthesise a silent placeholder instead:

```python
import numpy as np
import soundfile as sf

sf.write("sample_voice.wav", np.zeros(16000), 16000)
```

Any external WAV file can also be used; public domain samples are widely available online.

Generate a short sovereign voice sample from hexadecimal bytes and animate it:

```bash
python INANNA_AI_AGENT/inanna_ai.py --hex 00ff
```

```python
from pathlib import Path
from core.avatar_expression_engine import stream_avatar_audio

for _ in stream_avatar_audio(Path("qnl_hex_song.wav")):
    pass
```

## 2-D vs 3-D

Avatars can render with either a lightweight 2‑D placeholder or a simple 3‑D
scene derived from ``LargeWorldModel``. Select the mode per agent via the API:

```bash
curl -X POST /agents/overlord/avatar-mode -d '{"mode": "3d"}'
```

When ``mode`` is ``"3d"`` the video engine expects meshes, camera paths and
optional lip‑sync audio. These assets are loaded by
``media.avatar.lwm_renderer`` before frames are generated. Omitting the mode or
setting it to ``"2d"`` keeps the traditional flat rendering path.

### Frame Rendering Plug-ins

``core.video_engine`` exposes ``register_render_2d`` and ``register_render_3d``
hooks so external modules can override the default frame builders. Plug‑ins
provide callables with the same signature as the built‑in functions.

The ``media.avatar.lwm_renderer`` module registers an LWM‑driven renderer using
these hooks. Call ``configure_renderer()`` with mesh paths and optional
lip‑sync audio to supply camera trajectories and audio data before starting the
stream.

## Object-aware avatar selection

The video engine can adapt the visible avatar based on the current visual
context. A :class:`vision.yoloe_adapter.YOLOEAdapter` analyses incoming frames
and emits :class:`vision.yoloe_adapter.Detection` objects. These detections are
forwarded to :func:`agents.albedo.consume_detections`, which maps recognised
objects to avatar textures. For example, a ``"cat"`` detection selects
``avatars/cat.png`` while a ``"dog"`` detection loads ``avatars/dog.png``. When
no known objects are present the default texture is used. This allows external
scene objects to dynamically influence the avatar's appearance.

## 3-D mode

`LargeWorldModel` support enables a lightweight three‑dimensional workflow. Pass
an instance to :func:`src.media.avatar.generate_avatar` alongside captured frame
paths. The function builds a placeholder scene and returns a list of
``(x, y, z)`` camera coordinates synchronised with the frames. These coordinates
can drive simple camera motion during playback.

Required assets:

- a sequence of still frames representing the scene
- the built‑in ``src.lwm`` module; no external weights are needed

Example:

```python
from pathlib import Path
from src.lwm import LargeWorldModel
from src.media.avatar import generate_avatar
from core import video_engine

frames = [Path("frame1.png"), Path("frame2.png")]
audio, paths = generate_avatar(1000, frames, Path("out.mp4"), lwm_model=LargeWorldModel())
for frame in video_engine.generate_avatar_stream(camera_paths=paths):
    pass  # render or encode the frame
```

`generate_avatar_stream` highlights each camera position with a red pixel so
downstream renderers can align motion with the audio segment.

## Avatar Room

The game dashboard includes an **Avatar Room** for rapid operator interaction.
It displays the live WebRTC stream next to quick‑command buttons:

- **Wave** – invokes a simple greeting gesture.
- **Speak** – sends a short phrase for the avatar to voice.
- **Show Status** – fetches the avatar's current state and displays it.

A small chat pane relays operator questions to the sidekick helper which pulls
answers from the document registry.
