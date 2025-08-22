"""Utility functions for downloading model weights."""

from __future__ import annotations

import logging
import os
from pathlib import Path

try:  # pragma: no cover - package availability varies
    from huggingface_hub import snapshot_download
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "huggingface_hub is required for model downloads. "
        "Install it with `pip install huggingface_hub`."
    ) from exc

from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)


def download_deepseek() -> None:
    """Download the DeepSeek-R1 model to the local models directory."""
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if not token:
        LOGGER.error("HF_TOKEN environment variable not set")
        raise SystemExit("HF_TOKEN environment variable not set")

    target_dir = Path("INANNA_AI") / "models" / "DeepSeek-R1"
    try:
        snapshot_download(
            repo_id="deepseek-ai/DeepSeek-R1",
            token=token,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network failure
        LOGGER.exception("Model download failed: %s", exc)
        raise SystemExit(f"Model download failed: {exc}") from None
    else:
        LOGGER.info("Model downloaded to %s", target_dir)


def main() -> None:
    download_deepseek()


if __name__ == "__main__":
    main()
