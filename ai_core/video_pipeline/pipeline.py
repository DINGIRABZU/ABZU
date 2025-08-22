"""Video generation pipeline that selects processors based on a ``StyleConfig``."""
from __future__ import annotations

from style_engine.style_library import StyleConfig

from .pusa_v1_processor import PusaV1Processor
from .ltx_video_processor import LTXVideoProcessor


PROCESSOR_REGISTRY = {
    "pusa_v1": PusaV1Processor,
    "ltx": LTXVideoProcessor,
}


class VideoPipeline:
    """Pipeline that routes processing to the appropriate style processor."""

    def __init__(self, style_config: StyleConfig) -> None:
        self.style_config = style_config
        self.processor = self._select_processor(style_config.processor)

    def _select_processor(self, name: str):
        try:
            return PROCESSOR_REGISTRY[name]()
        except KeyError as exc:
            raise ValueError(f"Unknown processor: {name}") from exc

    def run(self, data):
        """Run the configured processor with the given data."""
        return self.processor.process(data)
