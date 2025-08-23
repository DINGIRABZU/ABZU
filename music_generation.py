"""Generate music from a text prompt using various models.

Wraps available Hugging Face pipelines to synthesize audio from textual
descriptions.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.media.audio import AudioProcessor

logger = logging.getLogger(__name__)

MODEL_IDS = {
    "musicgen": "facebook/musicgen-small",
    "riffusion": "riffusion/riffusion-model-v1",
    "musenet": "openai/musenet",
}

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


class MusicGenerator(AudioProcessor):
    """Generate music from a text prompt using transformer models."""

    def __init__(self, model: str = "musicgen") -> None:
        """Store the model identifier used for generation."""
        self.model = model

    def process(
        self,
        prompt: str,
        emotion: str | None = None,
        tempo: int | None = None,
    ) -> Path:
        """Generate audio from ``prompt`` and return the file path."""
        model_id = MODEL_IDS.get(self.model)
        if not model_id:
            raise ValueError(f"Unsupported model '{self.model}'")

        if emotion:
            prompt = f"{prompt} in a {emotion} mood"
        if tempo:
            prompt = f"{prompt} at {tempo} BPM"

        try:  # pragma: no cover - optional dependency
            from transformers import pipeline as hf_pipeline
        except Exception as exc:  # pragma: no cover - dependency guard
            raise ImportError("transformers is required for music generation") from exc

        pipe = hf_pipeline("text-to-audio", model=model_id)
        result = pipe(prompt)[0]
        audio: bytes = result.get("audio", b"")

        OUTPUT_DIR.mkdir(exist_ok=True)
        index = sum(1 for _ in OUTPUT_DIR.glob(f"{self.model}_*.wav"))
        out_file = OUTPUT_DIR / f"{self.model}_{index}.wav"
        out_file.write_bytes(audio)
        logger.info("Generated %s with %s", out_file, model_id)
        return out_file


def generate_from_text(
    prompt: str,
    model: str = "musicgen",
    emotion: str | None = None,
    tempo: int | None = None,
) -> Path:
    """Backward compatible wrapper around :class:`MusicGenerator`."""
    generator = MusicGenerator(model)
    return generator.process(prompt, emotion, tempo)


def main(argv: list[str] | None = None) -> None:
    """Command-line interface for music generation."""
    parser = argparse.ArgumentParser(description="Generate music from text")
    parser.add_argument("prompt", help="Description of the desired music")
    parser.add_argument(
        "--model",
        choices=list(MODEL_IDS),
        default="musicgen",
        help="Model to use (default: musicgen)",
    )
    parser.add_argument("--emotion", help="Optional emotion to guide style")
    parser.add_argument("--tempo", type=int, help="Optional tempo in BPM")
    args = parser.parse_args(argv)
    path = generate_from_text(args.prompt, args.model, args.emotion, args.tempo)
    print(path)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
