#!/bin/bash
# Basic setup script for Vast.ai instances
set -e

# install dependencies
if ! pip install -r requirements.txt; then
    echo "Failed to install Python packages" >&2
    exit 1
fi

# create directories for models and outputs
mkdir -p INANNA_AI/models
mkdir -p output

# optional model download
if [ "$1" = "--download" ]; then
    python download_models.py deepseek || true
fi
