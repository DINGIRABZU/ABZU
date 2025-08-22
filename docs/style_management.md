# Style Management

This document describes how to add new video styles to the system.

## Adding a Style Preset

1. **Create a YAML preset** under `style_engine/styles` with the style name.
   The file must define a `processor` field:
   ```yaml
   processor: my_style
   ```
2. **Update prompt presets** in `prompt_engineering.py` if the style requires
   custom prompt wording. Use `{prompt}` as a placeholder for the user input.
3. **Blend frames** using `style_engine.neural_style_transfer`. Provide a style
   embedding and call `apply_style_transfer` to process video frames.

## Example

```python
from prompt_engineering import apply_style_preset
from style_engine import neural_style_transfer

styled_prompt = apply_style_preset("render the scene", "my_style")
stylised_frames = neural_style_transfer.apply_style_transfer(frames, embedding)
```

This workflow ensures new styles can influence both text prompts and frame
appearance consistently.
