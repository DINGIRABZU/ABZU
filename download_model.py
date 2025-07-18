import os
from pathlib import Path
from huggingface_hub import snapshot_download
from dotenv import load_dotenv


def download_deepseek() -> None:
    """Download the DeepSeek-R1 model to the local models directory."""
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN environment variable not set")

    target_dir = Path("INANNA_AI") / "models" / "DeepSeek-R1"
    snapshot_download(
        repo_id="deepseek-ai/DeepSeek-R1",
        token=token,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )
    print(f"Model downloaded to {target_dir}")


def main() -> None:
    download_deepseek()


if __name__ == "__main__":
    main()
