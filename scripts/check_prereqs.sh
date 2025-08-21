#!/usr/bin/env bash
# Wrapper maintained for backward compatibility.
# Delegates to check_requirements.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/check_requirements.sh" "$@"
