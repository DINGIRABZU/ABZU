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
