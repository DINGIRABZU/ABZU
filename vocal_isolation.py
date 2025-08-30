"""Helpers for isolating vocals and other stems using external tools."""

from __future__ import annotations

__version__ = "0.1.0"

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

from src.media.audio.base import AudioProcessor

_DEF_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


def _collect_stems(out_dir: Path) -> Dict[str, Path]:
    stems: Dict[str, Path] = {}
    for file in out_dir.rglob("*"):
        if file.suffix.lower() in _DEF_AUDIO_EXTS:
            stems[file.stem] = file
    return stems


class VocalIsolator(AudioProcessor):
    """Separate audio files into stems using external tools."""

    def process(
        self,
        path: Path,
        method: str = "demucs",
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Separate ``path`` into stems with ``demucs``, ``spleeter`` or ``umx``."""
        out_dir = (
            Path(tempfile.mkdtemp(prefix="stems_"))
            if output_dir is None
            else output_dir
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        if method == "demucs":
            cmd = ["python3", "-m", "demucs.separate", "-o", str(out_dir), str(path)]
        elif method == "spleeter":
            cmd = [
                "spleeter",
                "separate",
                "-p",
                "spleeter:5stems",
                "-o",
                str(out_dir),
                str(path),
            ]
        elif method == "umx":
            cmd = ["umx", str(path), "--outdir", str(out_dir)]
        else:
            raise ValueError("method must be 'demucs', 'spleeter' or 'umx'")

        subprocess.run(cmd, check=True)
        return _collect_stems(out_dir)


def separate_stems(
    path: Path, method: str = "demucs", output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Backward compatible wrapper around :class:`VocalIsolator`."""
    isolator = VocalIsolator()
    return isolator.process(path, method, output_dir)


__all__ = ["separate_stems"]
