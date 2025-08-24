"""Generate a CycloneDX software bill of materials.

Run from the repository root:

    python scripts/generate_sbom.py --output sbom.json

The script requires the ``cyclonedx-bom`` package which provides the
``cyclonedx_py`` module. The resulting SBOM aids in supply-chain tracking.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a CycloneDX SBOM")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("sbom.json"),
        help="Output file path",
    )
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "cyclonedx_py",
        "environment",
        "-o",
        str(args.output),
    ]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("cyclonedx-bom is not installed", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(exc, file=sys.stderr)
        return exc.returncode

    print(f"SBOM written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
