"""CLI utilities for downloading model weights and dependencies.

The script handles fetching multiple model repositories and optional tools,
writing the resulting files to disk and invoking external installation
commands when required.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

from download_model import download_deepseek  # reuse logic

try:  # pragma: no cover - package availability varies
    from huggingface_hub import snapshot_download
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "huggingface_hub is required for model downloads. "
        "Install it with `pip install huggingface_hub`."
    ) from exc


LOG_PATH = Path("logs") / "model_audit.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

OLLAMA_INSTALL_URL = "https://ollama.ai/install.sh"
OLLAMA_INSTALL_SHA256 = (
    "9f5f4c4ed21821ba9b847bf3607ae75452283276cd8f52d2f2b38ea9f27af344"
)

MODEL_CHECKSUMS = {
    "gemma2": None,
    "glm41v_9b": None,
    "deepseek_v3": None,
    "mistral_8x22b": None,
    "kimi_k2": None,
}


def _get_hf_token() -> str:
    """Load the Hugging Face token from the environment."""
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN environment variable not set")
    return token


def _quantize_to_int8(model_dir: Path) -> None:
    """Quantize weights in place using bitsandbytes 8-bit loaders."""
    try:  # pragma: no cover - package availability varies
        from transformers import AutoModelForCausalLM
    except ImportError as exc:  # pragma: no cover - handled at runtime
        raise SystemExit(
            "transformers is required for quantization. "
            "Install it with `pip install transformers`."
        ) from exc

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir), device_map="auto", load_in_8bit=True
    )
    model.save_pretrained(str(model_dir))


def _download_with_hash(url: str, expected_hash: str, retries: int = 3) -> Path:
    """Download ``url`` verifying SHA256 ``expected_hash`` with retries."""
    for attempt in range(1, retries + 1):
        logger.info("Downloading %s (attempt %s/%s)", url, attempt, retries)
        try:
            with urllib.request.urlopen(url) as resp:  # pragma: no cover - network
                data = resp.read()
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("Download failed for %s: %s", url, exc)
            if attempt == retries:
                raise RuntimeError(f"Download failed for {url}: {exc}") from exc
            continue

        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_hash:
            logger.warning(
                "Hash mismatch for %s: expected %s, got %s", url, expected_hash, digest
            )
            if attempt == retries:
                raise RuntimeError(
                    f"Hash mismatch for {url}: expected {expected_hash}, got {digest}"
                )
            continue

        tmp_dir = Path(tempfile.mkdtemp())
        script_path = tmp_dir / "install.sh"
        script_path.write_bytes(data)
        logger.debug("Saved installer to %s", script_path)
        return script_path
    raise RuntimeError(f"Failed to download {url}")


def _verify_checksum(path: Path, expected_hash: str) -> None:
    """Validate SHA256 checksum of ``path`` against ``expected_hash``."""
    h = hashlib.sha256()
    if path.is_file():
        h.update(path.read_bytes())
    else:
        for file in sorted(p for p in path.rglob("*") if p.is_file()):
            h.update(file.read_bytes())
    digest = h.hexdigest()
    if digest != expected_hash:
        raise RuntimeError(
            f"Checksum mismatch for {path}: expected {expected_hash}, got {digest}"
        )
    logger.info("Checksum verified for %s", path)


def _install_ollama() -> None:
    script_path = _download_with_hash(OLLAMA_INSTALL_URL, OLLAMA_INSTALL_SHA256)
    try:
        subprocess.run(
            ["sh", str(script_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Ollama installation failed: %s", exc.stderr)
        raise RuntimeError(f"Ollama installation failed: {exc.stderr}") from exc
    logger.info("Ollama installation succeeded")


def download_gemma2() -> None:
    """Download the Gemma2 model using Ollama."""
    models_dir = Path("INANNA_AI") / "models"
    env = os.environ.copy()
    env["OLLAMA_MODELS"] = str(models_dir)

    if shutil.which("ollama") is None:
        logger.info("Ollama not found, installing")
        _install_ollama()

    try:
        subprocess.run(
            ["ollama", "pull", "gemma2"],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("Ollama pull failed: %s", exc.stderr)
        raise RuntimeError(f"Ollama pull failed: {exc.stderr}") from exc
    expected = MODEL_CHECKSUMS.get("gemma2")
    target = models_dir / "gemma2"
    if expected:
        _verify_checksum(target, expected)
    logger.info("Model downloaded to %s", target)
    print(f"Model downloaded to {target}")


def download_glm41v_9b(int8: bool = False) -> None:
    """Download GLM-4.1V-9B from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "GLM-4.1V-9B"
    try:
        snapshot_download(
            repo_id="THUDM/glm-4.1v-9b",
            token=token,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Model download failed: %s", exc)
        raise SystemExit(f"Model download failed: {exc}") from None
    expected = MODEL_CHECKSUMS.get("glm41v_9b")
    if expected:
        _verify_checksum(target_dir, expected)
    if int8:
        _quantize_to_int8(target_dir)
    logger.info("Model downloaded to %s", target_dir)
    print(f"Model downloaded to {target_dir}")


def download_deepseek_v3(int8: bool = False) -> None:
    """Download DeepSeek-V3 from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "DeepSeek-V3"
    try:
        snapshot_download(
            repo_id="deepseek-ai/DeepSeek-V3",
            token=token,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Model download failed: %s", exc)
        raise SystemExit(f"Model download failed: {exc}") from None
    expected = MODEL_CHECKSUMS.get("deepseek_v3")
    if expected:
        _verify_checksum(target_dir, expected)
    if int8:
        _quantize_to_int8(target_dir)
    logger.info("Model downloaded to %s", target_dir)
    print(f"Model downloaded to {target_dir}")


def download_mistral_8x22b(int8: bool = False) -> None:
    """Download Mistral 8x22B from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "Mistral-8x22B"
    try:
        snapshot_download(
            repo_id="mistralai/Mixtral-8x22B",
            token=token,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Model download failed: %s", exc)
        raise SystemExit(f"Model download failed: {exc}") from None
    expected = MODEL_CHECKSUMS.get("mistral_8x22b")
    if expected:
        _verify_checksum(target_dir, expected)
    if int8:
        _quantize_to_int8(target_dir)
    logger.info("Model downloaded to %s", target_dir)
    print(f"Model downloaded to {target_dir}")


def download_kimi_k2(int8: bool = False) -> None:
    """Download Kimi-K2 from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "Kimi-K2"
    try:
        snapshot_download(
            repo_id="Fox-Kimi/Kimi-K2",
            token=token,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Model download failed: %s", exc)
        raise SystemExit(f"Model download failed: {exc}") from None
    expected = MODEL_CHECKSUMS.get("kimi_k2")
    if expected:
        _verify_checksum(target_dir, expected)
    if int8:
        _quantize_to_int8(target_dir)
    logger.info("Model downloaded to %s", target_dir)
    print(f"Model downloaded to {target_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Model downloader")
    subparsers = parser.add_subparsers(dest="model", help="Model to download")

    subparsers.add_parser("deepseek", help="Download DeepSeek-R1 from Hugging Face")
    subparsers.add_parser("gemma2", help="Download Gemma2 via Ollama")
    p = subparsers.add_parser("glm41v_9b", help="Download GLM-4.1V-9B")
    p.add_argument("--int8", action="store_true", help="Quantize with bitsandbytes")
    p = subparsers.add_parser("deepseek_v3", help="Download DeepSeek-V3")
    p.add_argument("--int8", action="store_true", help="Quantize with bitsandbytes")
    p = subparsers.add_parser("mistral_8x22b", help="Download Mistral 8x22B")
    p.add_argument("--int8", action="store_true", help="Quantize with bitsandbytes")
    p = subparsers.add_parser("kimi_k2", help="Download Kimi-K2")
    p.add_argument("--int8", action="store_true", help="Quantize with bitsandbytes")

    args = parser.parse_args()
    if args.model == "deepseek":
        download_deepseek()
    elif args.model == "gemma2":
        download_gemma2()
    elif args.model == "glm41v_9b":
        download_glm41v_9b(int8=args.int8)
    elif args.model == "deepseek_v3":
        download_deepseek_v3(int8=args.int8)
    elif args.model == "mistral_8x22b":
        download_mistral_8x22b(int8=args.int8)
    elif args.model == "kimi_k2":
        download_kimi_k2(int8=args.int8)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
