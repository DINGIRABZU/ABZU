#!/bin/bash
# Verify that required external commands are available
set -e

missing=()
for cmd in docker nc sox ffmpeg; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        missing+=("$cmd")
    fi
done

if [ "${#missing[@]}" -ne 0 ]; then
    echo "Missing required command(s): ${missing[*]}" >&2
    exit 1
fi

printf "All prerequisites satisfied.\n"
