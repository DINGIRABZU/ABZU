from __future__ import annotations

"""Generate music from a text prompt using various models."""

from pathlib import Path
import argparse
import logging

try:  # pragma: no cover - optional dependency
    from transformers import pipeline as hf_pipeline
except Exception:  # pragma: no cover - transformers may be missing
    hf_pipeline = None  # type: ignore

logger = logging.getLogger(__name__)

MODEL_IDS = {
    "musicgen": "facebook/musicgen-small",
    "riffusion": "riffusion/riffusion-model-v1",
    "musenet": "openai/musenet",
}

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def generate_from_text(prompt: str, model: str = "musicgen") -> Path:
    """Generate audio from ``prompt`` and return the file path."""
    model_id = MODEL_IDS.get(model)
    if not model_id:
        raise ValueError(f"Unsupported model '{model}'")

    if hf_pipeline is None:
        raise ImportError("transformers is required for music generation")

    pipe = hf_pipeline("text-to-audio", model=model_id)
    result = pipe(prompt)[0]
    audio: bytes = result.get("audio", b"")

    OUTPUT_DIR.mkdir(exist_ok=True)
    index = sum(1 for _ in OUTPUT_DIR.glob(f"{model}_*.wav"))
    out_file = OUTPUT_DIR / f"{model}_{index}.wav"
    out_file.write_bytes(audio)
    logger.info("Generated %s with %s", out_file, model_id)
    return out_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate music from text")
    parser.add_argument("prompt", help="Description of the desired music")
    parser.add_argument(
        "--model",
        choices=list(MODEL_IDS),
        default="musicgen",
        help="Model to use (default: musicgen)",
    )
    args = parser.parse_args(argv)
    path = generate_from_text(args.prompt, args.model)
    print(path)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
