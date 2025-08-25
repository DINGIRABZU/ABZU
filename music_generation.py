"""Generate music from a text prompt using various models.

Wraps available Hugging Face pipelines to synthesize audio from textual
descriptions.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, Iterator

from src.media.audio.base import AudioProcessor

try:  # pragma: no cover - optional dependency
    from transformers import pipeline as hf_pipeline  # type: ignore
except Exception:  # pragma: no cover - dependency guard
    hf_pipeline = None  # type: ignore

logger = logging.getLogger(__name__)

MODEL_IDS = {
    "musicgen": "facebook/musicgen-small",
    "riffusion": "riffusion/riffusion-model-v1",
    "musenet": "openai/musenet",
}

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def _resolve_model_id(model: str) -> str:
    """Return the full model identifier for ``model``.

    ``model`` may be a key in :data:`MODEL_IDS` or a direct Hugging Face
    identifier. A :class:`ValueError` is raised when the value is empty.
    """

    model_id = MODEL_IDS.get(model, model)
    if not model_id:
        raise ValueError("Model name cannot be empty")
    return model_id


def _validate_params(
    temperature: float,
    duration: int,
    tempo: int | None,
    seed: int | None,
) -> None:
    """Validate generation parameters and raise :class:`ValueError` on error."""

    if not (0 < temperature <= 2):
        raise ValueError("temperature must be between 0 and 2")
    if duration <= 0:
        raise ValueError("duration must be positive")
    if tempo is not None and tempo <= 0:
        raise ValueError("tempo must be positive")
    if seed is not None and seed < 0:
        raise ValueError("seed must be non-negative")


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
        *,
        temperature: float = 1.0,
        duration: int = 5,
        seed: int | None = None,
        stream: bool = False,
    ) -> Path | Iterable[bytes]:
        """Generate audio from ``prompt``.

        When ``stream`` is ``True`` the method returns an iterator yielding
        audio chunks as ``bytes``. Otherwise it returns the path to the written
        WAV file.
        """
        model_id = _resolve_model_id(self.model)

        if emotion:
            prompt = f"{prompt} in a {emotion} mood"
        if tempo:
            prompt = f"{prompt} at {tempo} BPM"

        _validate_params(temperature, duration, tempo, seed)

        if hf_pipeline is None:
            raise ImportError("transformers is required for music generation")

        pipe = hf_pipeline("text-to-audio", model=model_id)
        gen_params = {
            "temperature": temperature,
            "duration": duration,
            "stream": stream,
        }
        if seed is not None:
            gen_params["seed"] = seed

        result = pipe(prompt, **gen_params)
        if stream:
            def _stream() -> Iterator[bytes]:
                for chunk in result:
                    yield chunk.get("audio", b"")

            return _stream()

        first = next(iter(result))
        audio: bytes = first.get("audio", b"")

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
    *,
    temperature: float = 1.0,
    duration: int = 5,
    seed: int | None = None,
    stream: bool = False,
) -> Path | Iterable[bytes]:
    """Backward compatible wrapper around :class:`MusicGenerator`."""
    generator = MusicGenerator(model)
    return generator.process(
        prompt,
        emotion,
        tempo,
        temperature=temperature,
        duration=duration,
        seed=seed,
        stream=stream,
    )


def main(argv: list[str] | None = None) -> None:
    """Command-line interface for music generation."""
    parser = argparse.ArgumentParser(description="Generate music from text")
    parser.add_argument("prompt", help="Description of the desired music")
    parser.add_argument(
        "--model",
        default="musicgen",
        help=
        "Model key or HF id (default: musicgen). Available keys: "
        + ", ".join(MODEL_IDS),
    )
    parser.add_argument("--emotion", help="Optional emotion to guide style")
    parser.add_argument("--tempo", type=int, help="Optional tempo in BPM")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature")
    parser.add_argument("--duration", type=int, default=5, help="Approximate duration in seconds")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--stream", action="store_true", help="Stream audio chunks to stdout")
    args = parser.parse_args(argv)

    result = generate_from_text(
        args.prompt,
        args.model,
        args.emotion,
        args.tempo,
        temperature=args.temperature,
        duration=args.duration,
        seed=args.seed,
        stream=args.stream,
    )
    if args.stream:
        import sys

        for chunk in result:  # type: ignore[assignment]
            sys.stdout.buffer.write(chunk)
    else:
        print(result)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
