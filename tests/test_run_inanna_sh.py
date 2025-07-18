import os
import sys
import subprocess
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _create_stub_python(tmp_path: Path, record: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "python"
    stub.write_text(
        f"#!/bin/sh\n" \
        f"if [ \"$1\" = \"INANNA_AI_AGENT/inanna_ai.py\" ]; then\n" \
        f"  echo \"$@\" > \"{record}\"\n" \
        f"fi\n"
    )
    stub.chmod(0o755)
    return bin_dir


def _symlink_models(repo_root: Path, models_dir: Path) -> tuple[Path, Path | None]:
    target = repo_root / "INANNA_AI" / "models"
    backup = None
    if target.exists() or target.is_symlink():
        backup = target.with_name("models.bak")
        target.rename(backup)
    target.symlink_to(models_dir, target_is_directory=True)
    return target, backup


def _restore_symlink(target: Path, backup: Path | None) -> None:
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    if backup:
        backup.rename(target)


def test_run_inanna_invokes_chat(tmp_path):
    models_dir = tmp_path / "models"
    (models_dir / "DeepSeek-R1").mkdir(parents=True)
    record = tmp_path / "args.txt"
    stub_dir = _create_stub_python(tmp_path, record)
    target, backup = _symlink_models(ROOT, models_dir)

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["PYTHONPATH"] = str(ROOT)

    try:
        result = subprocess.run(
            ["bash", str(ROOT / "run_inanna.sh"), "--model-dir", str(models_dir)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
    finally:
        _restore_symlink(target, backup)

    assert result.returncode == 0
    assert record.exists()
    args = record.read_text().split()
    assert args[0] == "INANNA_AI_AGENT/inanna_ai.py"
    assert args[1] == "chat"
    assert args[2:] == ["--model-dir", str(models_dir)]


def test_run_inanna_exits_when_models_missing(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True)
    record = tmp_path / "args.txt"
    stub_dir = _create_stub_python(tmp_path, record)
    target, backup = _symlink_models(ROOT, models_dir)

    env = os.environ.copy()
    env["PATH"] = f"{stub_dir}:{env['PATH']}"
    env["PYTHONPATH"] = str(ROOT)

    try:
        result = subprocess.run(
            ["bash", str(ROOT / "run_inanna.sh")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
    finally:
        _restore_symlink(target, backup)

    assert result.returncode == 1
    assert "Required model files" in result.stderr
    assert not record.exists()

