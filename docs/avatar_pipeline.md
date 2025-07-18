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
