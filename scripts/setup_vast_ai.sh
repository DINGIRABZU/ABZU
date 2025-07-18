#!/bin/bash
# Basic setup script for Vast.ai instances
set -e

# install dependencies
pip install -r requirements.txt

# create directories for models and outputs
mkdir -p INANNA_AI/models
mkdir -p output

# placeholder model download (optional)
if [ "$1" = "--download" ]; then
    python download_models.py deepseek || true
fi
