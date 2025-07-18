import argparse
import os
import shutil
import subprocess
from pathlib import Path

from download_model import download_deepseek  # reuse logic
from dotenv import load_dotenv
from huggingface_hub import snapshot_download


def _get_hf_token() -> str:
    """Load the Hugging Face token from the environment."""
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN environment variable not set")
    return token


def _quantize_to_int8(model_dir: Path) -> None:
    """Quantize weights in place using bitsandbytes 8-bit loaders."""
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir), device_map="auto", load_in_8bit=True
    )
    model.save_pretrained(str(model_dir))


def download_gemma2() -> None:
    """Download the Gemma2 model using Ollama."""
    models_dir = Path("INANNA_AI") / "models"
    env = os.environ.copy()
    env["OLLAMA_MODELS"] = str(models_dir)

    if shutil.which("ollama") is None:
        print("Ollama not found, installing...")
        subprocess.run(
            "curl -fsSL https://ollama.ai/install.sh | sh",
            shell=True,
            check=True,
        )

    subprocess.run(["ollama", "pull", "gemma2"], check=True, env=env)
    print(f"Model downloaded to {models_dir / 'gemma2'}")


def download_glm41v_9b(int8: bool = False) -> None:
    """Download GLM-4.1V-9B from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "GLM-4.1V-9B"
    snapshot_download(
        repo_id="THUDM/glm-4.1v-9b",
        token=token,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )
    if int8:
        _quantize_to_int8(target_dir)
    print(f"Model downloaded to {target_dir}")


def download_deepseek_v3(int8: bool = False) -> None:
    """Download DeepSeek-V3 from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "DeepSeek-V3"
    snapshot_download(
        repo_id="deepseek-ai/DeepSeek-V3",
        token=token,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )
    if int8:
        _quantize_to_int8(target_dir)
    print(f"Model downloaded to {target_dir}")


def download_mistral_8x22b(int8: bool = False) -> None:
    """Download Mistral 8x22B from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "Mistral-8x22B"
    snapshot_download(
        repo_id="mistralai/Mixtral-8x22B",
        token=token,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )
    if int8:
        _quantize_to_int8(target_dir)
    print(f"Model downloaded to {target_dir}")


def download_kimi_k2(int8: bool = False) -> None:
    """Download Kimi-K2 from Hugging Face and optionally quantize."""
    token = _get_hf_token()
    target_dir = Path("INANNA_AI") / "models" / "Kimi-K2"
    snapshot_download(
        repo_id="Fox-Kimi/Kimi-K2",
        token=token,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )
    if int8:
        _quantize_to_int8(target_dir)
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

