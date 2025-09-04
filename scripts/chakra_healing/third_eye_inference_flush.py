#!/usr/bin/env python3
"""Clear model queue and hot-reload model."""

from __future__ import annotations

import subprocess


def main() -> None:
    subprocess.run(["pkill", "-f", "model_queue"], check=False)


if __name__ == "__main__":
    main()
