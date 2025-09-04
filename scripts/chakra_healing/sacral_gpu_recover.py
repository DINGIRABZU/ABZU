#!/usr/bin/env python3
"""Reset GPU VRAM or pause GPU tasks."""

from __future__ import annotations

import subprocess


def main() -> None:
    cmd = ["nvidia-smi", "--gpu-reset"]
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
