# Avatar Visual Customization

This guide outlines how to turn a 2D concept image into the 3D model used by the video engine.

## 1. Provide a reference image

Place a front-facing sketch or photo of your character under `INANNA_AI/AVATAR/`.
This image will serve as the texture or modelling reference.

## 2. Run the 2D → 3D pipeline

1. Open Blender and load `INANNA_AI/AVATAR/avatar_builder/rigging_config.blend`.
2. Import your reference image as a plane or use it as a texture.
3. Model the head and body geometry around the image.
4. Use **Auto‑Rig Pro** to generate a rig. The quick rig tool can align the mesh
   to a template skeleton and create weight paints automatically.
5. Export the finished mesh (for example as `avatar.glb`) back into
   `INANNA_AI/AVATAR/` for later loading.

## 3. Edit `avatar_config.toml`

Adjust basic traits that the video engine reads at runtime:

```toml
# guides/avatar_config.toml
eye_color = [0, 128, 255]
sigil = "spiral"
```

- `eye_color` controls the RGB fill used for the avatar's eyes.
- `sigil` sets the symbol overlay that appears in each frame.

Save the file after editing and restart any running scripts to apply the new
traits.

## 4. Asset requirements

The avatar pipeline expects a small set of support assets:

- **Skins and overlays** – additional PNG images or CSS classes can be
  referenced from `avatar_config.toml` under the `skins` table. Place image
  files alongside your model in `INANNA_AI/AVATAR/`.
- **Style cues** – real‑time style changes sent by the language model or audio
  mixer are mapped to CSS classes named `style-<cue>` in the web console. Add
  matching rules to your console stylesheet or provide overlay images.
- **Audio hooks** – when streaming audio with `stream_avatar_audio` the engine
  analyses tempo and intensity to drive mouth motion and visual bars. Ensure
  the WAV file is available on disk before starting playback.

## 5. Real‑time configuration

`video_stream.AvatarVideoTrack` accepts an optional `asyncio.Queue[str]` of
style cues. Push short tokens such as `"glitch"` or `"calm"` to the queue to
change the avatar's appearance while streaming. The web console listens for
these cues over the WebRTC data channel and updates the video element's CSS
class accordingly.
