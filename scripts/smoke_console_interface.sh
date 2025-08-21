#!/bin/bash
# Smoke test for the Crown console interface.
#
# Manual steps:
#   1. Run this script.
#   2. Review the usage message printed by the module.
#      If the message appears without errors, the import succeeded.
#
# No interactive input is required.
set -euo pipefail
python -m cli.console_interface --help
