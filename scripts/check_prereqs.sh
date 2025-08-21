#!/bin/bash
# Verify that required external commands are available
set -e

missing=0

for cmd in docker nc sox ffmpeg curl jq wget aria2c; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required command: $cmd" >&2
        missing=1
    fi
done

if [ "$missing" -ne 0 ]; then
    exit 1
fi

printf "All prerequisites satisfied.\n"
