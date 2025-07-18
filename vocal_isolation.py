from __future__ import annotations

"""Helpers for isolating vocals and other stems using external tools."""

from pathlib import Path
from typing import Dict, Optional
import subprocess
import tempfile


_DEF_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


def _collect_stems(out_dir: Path) -> Dict[str, Path]:
    stems: Dict[str, Path] = {}
    for file in out_dir.rglob('*'):
        if file.suffix.lower() in _DEF_AUDIO_EXTS:
            stems[file.stem] = file
    return stems


def separate_stems(
    path: Path, method: str = "demucs", output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Separate ``path`` into stems with ``demucs``, ``spleeter`` or ``umx``.

    Parameters
    ----------
    path:
        Audio file to process.
    method:
        ``"demucs"`` (default), ``"spleeter"`` or ``"umx"``.
    output_dir:
        Directory to write stems to. Uses a temporary directory if not
        provided.

    Returns
    -------
    Dict[str, Path]
        Mapping of stem name to file path in a temporary directory.
    """
    out_dir = Path(tempfile.mkdtemp(prefix="stems_")) if output_dir is None else output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if method == "demucs":
        cmd = ["python3", "-m", "demucs.separate", "-o", str(out_dir), str(path)]
    elif method == "spleeter":
        cmd = ["spleeter", "separate", "-p", "spleeter:5stems", "-o", str(out_dir), str(path)]
    elif method == "umx":
        cmd = ["umx", str(path), "--outdir", str(out_dir)]
    else:
        raise ValueError("method must be 'demucs', 'spleeter' or 'umx'")

    subprocess.run(cmd, check=True)
    return _collect_stems(out_dir)


__all__ = ["separate_stems"]
