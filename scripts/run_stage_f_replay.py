#!/usr/bin/env python3
"""Placeholder entry point for Stage F hardware replay automation."""

from __future__ import annotations

import sys
from textwrap import dedent


def main() -> int:
    """Emit an environment-limited notice until hardware access is available."""

    message = dedent(
        """
        environment-limited: stage-f replay requires a reserved gate-runner window.

        Planned execution flow once hardware access is restored:
          1. Validate the sandbox evidence bundle:
               - Stage C readiness packet
               - Stage B rotation ledger
               - Stage E transport snapshot
             Stage the resulting manifest for upload.
          2. Reserve the Stage F gate-runner slot and provision the Neo-APSU toolchain.
             Sync parity binaries to the hardware workspace.
          3. Invoke the Neo-APSU replay routines on hardware. Stream parity traces and
             rollback drills into the Stage F evidence bundle.
             Capture approvals before updating roadmap and status ledgers.
        """
    ).strip()

    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
