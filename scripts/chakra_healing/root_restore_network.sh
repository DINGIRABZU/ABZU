#!/usr/bin/env bash
# Restart network interface or reduce disk I/O.
set -euo pipefail

if command -v systemctl >/dev/null 2>&1; then
  systemctl restart networking || systemctl restart NetworkManager || true
fi

sync || true
