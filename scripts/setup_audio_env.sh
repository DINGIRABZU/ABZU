#!/usr/bin/env bash
# Install pinned audio dependencies
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

pip install \
  librosa==0.11.0 \
  soundfile==0.13.1 \
  opensmile==2.6.0 \
  clap==0.7 \
  rave==1.0.0
