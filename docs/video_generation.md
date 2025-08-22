# Video Generation Pipeline

This document outlines the simplified video generation pipeline and how styles
are configured.

## Pipeline Stages

1. **Load Style** – `style_engine.style_library.load_style_config` reads a YAML
   preset and returns a `StyleConfig` with the processor name.
2. **Initialise Pipeline** – `ai_core.video_pipeline.pipeline.VideoPipeline`
   receives the `StyleConfig` and instantiates the matching processor.
3. **Process Data** – The selected processor's `process` method handles the
   incoming data and produces the output.

## Adding New Styles

1. Create a processor module in `ai_core/video_pipeline/` implementing a
   `process(data)` method.
2. Register the processor in `ai_core/video_pipeline/pipeline.py` within the
   `PROCESSOR_REGISTRY`.
3. Add a YAML preset in `style_engine/styles/` naming the processor:

   ```yaml
   processor: my_new_processor
   ```
4. Load the style using `load_style_config("my_new_processor")` and run the
   pipeline.
