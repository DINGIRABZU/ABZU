#!/usr/bin/env bash
# Install development/test dependencies.
# Warn about large packages like PyTorch and transformers.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cat <<'MSG'
This will install all development and test packages listed in dev-requirements.txt.
Some packages such as torch and transformers are large and may take several minutes.
MSG

read -p "Proceed with installation? [y/N] " ans
case "$ans" in
  y|Y ) ;;
  * ) echo "Aborted."; exit 1;;
esac

pip install -r "$ROOT_DIR/dev-requirements.txt"

