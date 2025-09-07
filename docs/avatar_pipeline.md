# Avatar Pipeline

The avatar pipeline synchronises generated speech with visual animation. It reads
configuration from `guides/avatar_config.toml` and produces frames via
`core.video_engine`.

## Setup

Install the Python requirements and optional packages for lip sync:

```bash
pip install -r SPIRAL_OS/requirements.txt
```

`SadTalker`, `Wav2Lip` and `ControlNet` are optional but provide advanced
animation when available.

When the optional **SadTalker** package is installed the video engine generates
frames directly from the speech sample. If not available it falls back to
**Wav2Lip** when present or a minimal mouth overlay.

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

Any external WAV file can also be used; public domain samples are available at
[https://people.sc.fsu.edu/~jburkardt/data/wav/](https://people.sc.fsu.edu/~jburkardt/data/wav/).

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
