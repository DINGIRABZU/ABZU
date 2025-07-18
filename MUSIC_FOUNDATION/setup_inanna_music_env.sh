#!/bin/bash

echo "🌸 Initiating INANNA_MUSIC_ENV setup..."
echo "🔍 Checking Python version..."
python3 --version

echo "📦 Installing required Python packages..."
pip install --upgrade pip
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pip install -r "$SCRIPT_DIR/REQUIREMENTS_Music_Foundation.txt"

echo "🌀 Creating workspace directories..."
mkdir -p output/qnl
mkdir -p logs
mkdir -p audio_samples

echo "✅ INANNA_MUSIC_ENV is ready."
echo "✨ You may now run: python3 music_foundation.py path_to_song.mp3"
