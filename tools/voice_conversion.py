from __future__ import annotations

"""Command line wrappers for voice conversion tools."""

from pathlib import Path
import subprocess
import tempfile


def apply_rvc(input_wav: Path, preset: str) -> Path:
    """Run an RVC conversion ``preset`` on ``input_wav``.

    Returns the path to the converted file within a temporary directory.
    """
    out_dir = Path(tempfile.mkdtemp(prefix="rvc_"))
    out_path = out_dir / input_wav.name
    cmd = [
        "rvc",
        "--preset",
        preset,
        "--input",
        str(input_wav),
        "--output",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path


def voicefix(path: Path) -> Path:
    """Clean up ``path`` using the VoiceFixer binary."""
    out_path = path.with_name(f"{path.stem}_vf.wav")
    cmd = ["voicefixer", "-i", str(path), "-o", str(out_path)]
    subprocess.run(cmd, check=True)
    return out_path


__all__ = ["apply_rvc", "voicefix"]
