"""Interactive quick-start wizard for ABZU."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIRM = ROOT / "onboarding_confirm.yml"
NEO_APSU_DOCS = [
    "NEOABZU/docs/onboarding.md",
    "NEOABZU/docs/Oroboros_Core.md",
    "NEOABZU/docs/migration_crosswalk.md",
]


def run_command(cmd: List[str], dry_run: bool) -> None:
    """Execute a command or print it when ``dry_run`` is True."""
    if dry_run:
        print("DRY RUN:", " ".join(cmd))
    else:
        subprocess.run(cmd, check=True)


def clone_repo(
    repo_url: str = "https://github.com/your-org/ABZU.git",
    destination: str = "ABZU",
    dry_run: bool = False,
) -> None:
    """Clone the ABZU repository to ``destination``."""
    run_command(["git", "clone", repo_url, destination], dry_run)


def create_virtualenv(env_path: str = ".venv", dry_run: bool = False) -> None:
    """Create a Python virtual environment at ``env_path``."""
    run_command(["python", "-m", "venv", env_path], dry_run)


def run_setup_script(
    script: str = "scripts/easy_setup.sh", dry_run: bool = False
) -> None:
    """Run the repository setup script."""
    run_command([script], dry_run)


def download_model(model: str, int8: bool = True, dry_run: bool = False) -> None:
    """Download model weights using ``download_models.py``."""
    cmd = ["python", "download_models.py", model]
    if int8:
        cmd.append("--int8")
    run_command(cmd, dry_run)


def run_smoke_tests(dry_run: bool = False) -> None:
    """Run a basic smoke test for the console interface."""
    run_command(["bash", "scripts/smoke_console_interface.sh"], dry_run)


def sha256(path: Path) -> str:
    """Return the SHA256 hash of ``path``."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confirm_docs(signer: str) -> None:
    """Prompt for Neo-APSU document confirmations and record them."""
    data = {}
    if CONFIRM.exists():
        data = yaml.safe_load(CONFIRM.read_text()) or {}
    docs = data.setdefault("documents", {})
    for rel in NEO_APSU_DOCS:
        answer = input(f"Confirm you've read {rel}? [y]/n: ") or "y"
        if answer.lower() not in {"y", "yes"}:
            continue
        purpose = input("  Purpose: ")
        scope = input("  Scope: ")
        key_rules = input("  Key rules: ")
        insight = input("  Insight: ")
        docs[rel] = {
            "sha256": sha256(ROOT / rel),
            "summary": {
                "purpose": purpose,
                "scope": scope,
                "key_rules": key_rules,
                "insight": insight,
            },
            "signed_by": signer,
            "signed_at": datetime.utcnow().isoformat() + "Z",
        }
    CONFIRM.write_text(yaml.safe_dump(data, sort_keys=True))


def main() -> None:
    """Launch the interactive quick-start wizard."""
    parser = argparse.ArgumentParser(description="Run ABZU setup steps interactively.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands instead of executing them",
    )
    args = parser.parse_args()

    repo_url = (
        input("Repository URL [https://github.com/your-org/ABZU.git]: ")
        or "https://github.com/your-org/ABZU.git"
    )
    destination = input("Clone destination [ABZU]: ") or "ABZU"
    clone_repo(repo_url, destination, args.dry_run)

    env_path = input("Virtual environment path [.venv]: ") or ".venv"
    create_virtualenv(env_path, args.dry_run)

    script = input("Setup script [scripts/easy_setup.sh]: ") or "scripts/easy_setup.sh"
    run_setup_script(script, args.dry_run)

    model = input("Model to download [glm41v_9b]: ") or "glm41v_9b"
    int8_answer = input("Use int8 quantization? [y]/n: ") or "y"
    download_model(model, int8_answer.lower() in {"y", "yes"}, args.dry_run)

    run_test = input("Run smoke console test? [y]/n: ") or "y"
    if run_test.lower() in {"y", "yes"}:
        run_smoke_tests(args.dry_run)

    signer = input("Name to sign onboarding confirmations: ") or "anonymous"
    confirm_docs(signer)


if __name__ == "__main__":
    main()
