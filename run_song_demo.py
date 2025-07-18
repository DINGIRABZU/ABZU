#!/usr/bin/env python3
"""Demo runner for INANNA Music Composer AI.

This script analyzes a local MP3 or WAV file using
``inanna_music_COMPOSER_ai.py`` and prints the resulting QNL phrases.
"""

import argparse
from pathlib import Path
import yaml

from MUSIC_FOUNDATION.inanna_music_COMPOSER_ai import (
    InannaMusicInterpreter,
    export_qnl,
)
from MUSIC_FOUNDATION.qnl_utils import generate_qnl_structure


CONFIG_PATH = Path(__file__).resolve().parent / "voice_config.yaml"


def load_voice_config(path: Path = CONFIG_PATH) -> dict:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {k.lower(): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a local audio file and display QNL output"
    )
    parser.add_argument("audio_file", help="Path to a local MP3 or WAV file")
    parser.add_argument(
        "--preview", default="output/preview.wav", help="Preview WAV file path"
    )
    parser.add_argument(
        "--json", default="output/qnl_7plane.json", help="QNL JSON output path"
    )
    parser.add_argument("--tone", help="Personality tone from voice_config")
    args = parser.parse_args()

    engine = InannaMusicInterpreter(args.audio_file)
    engine.load_audio()
    chroma = engine.analyze()
    planes = engine.analyze_planes()
    engine.export_preview(args.preview)

    voice_cfg = {}
    if args.tone:
        voice_cfg = load_voice_config().get(args.tone.lower(), {})

    qnl_data = generate_qnl_structure(
        chroma,
        engine.tempo,
        metadata={"source": args.audio_file},
        planes=planes,
    )
    export_qnl(qnl_data, args.json)

    if voice_cfg:
        print("Voice settings:", voice_cfg)

    print("QNL Output:")
    for phrase in qnl_data["qnl_output"]:
        print(" -", phrase)


if __name__ == "__main__":
    main()
