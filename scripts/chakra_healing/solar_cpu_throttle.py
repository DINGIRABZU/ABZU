#!/usr/bin/env python3
"""Cap runaway CPU processes via cgroups."""

from __future__ import annotations

import subprocess


def main() -> None:
    cmd = ["cgset", "-r", "cpu.shares=512", "system.slice"]
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
