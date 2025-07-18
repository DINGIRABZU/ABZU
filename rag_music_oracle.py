from __future__ import annotations

"""Music oracle that mixes RAG search with audio emotion analysis."""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import argparse

import rag_engine
from INANNA_AI import emotion_analysis
import play_ritual_music


def analyze_audio(path: Path) -> Dict[str, Any]:
    """Return emotion information extracted from ``path``."""
    return emotion_analysis.analyze_audio_emotion(str(path))


def search_corpus(question: str, features: Dict[str, Any]) -> List[Any]:
    """Query the music corpus for ``question`` enriched with ``features``."""
    extras = ""
    if features:
        extras = (
            f" emotion:{features.get('emotion')}"
            f" tempo:{features.get('tempo')}"
            f" pitch:{features.get('pitch')}"
        )
    return rag_engine.query(question + extras)


def answer(
    question: str,
    audio: Path | None = None,
    *,
    play: bool = False,
    ritual: str = "\u2609",
) -> Tuple[str, Optional[Path]]:
    """Return text and optional ritual music answering ``question``."""
    features: Dict[str, Any] = {}
    if audio:
        features = analyze_audio(audio)
    results = search_corpus(question, features)
    snippet = ""
    if results:
        item = results[0]
        if isinstance(item, dict):
            snippet = item.get("snippet", "")
        else:
            snippet = getattr(item, "content", getattr(getattr(item, "node", None), "text", ""))
    text = ""
    if features:
        text = (
            f"Detected emotion {features['emotion']} at {features['tempo']} BPM. "
        )
    text += snippet or "No related passages found."

    out_path: Optional[Path] = None
    if play and features:
        arch = emotion_analysis.emotion_to_archetype(features["emotion"])
        out_path = play_ritual_music.compose_ritual_music(
            features["emotion"], ritual, archetype=arch
        )
    return text, out_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag_music_oracle")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("--audio", help="Path to an audio file")
    parser.add_argument("--play", action="store_true", help="Play ritual response")
    parser.add_argument("--ritual", default="\u2609", help="Ritual symbol")
    args = parser.parse_args(argv)

    audio_path = Path(args.audio) if args.audio else None
    text, out = answer(args.question, audio_path, play=args.play, ritual=args.ritual)
    print(text)
    if out:
        print(f"Audio response written to {out}")
    return 0


__all__ = ["answer", "main", "analyze_audio", "search_corpus"]


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())

