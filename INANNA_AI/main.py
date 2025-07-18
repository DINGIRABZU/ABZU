from __future__ import annotations

"""Command line interface for INANNA AI.

This tool runs the interactive voice loop and also exposes ingestion helpers to
fetch external texts.  The ``fetch-gutenberg`` and ``fetch-github`` subcommands
download materials used for learning while ``voice`` starts the normal Albedo
conversation flow.
"""

import argparse
import numpy as np
from orchestrator import MoGEOrchestrator
from crown_router import route_decision
from .personality_layers import REGISTRY, list_personalities
from .rfa_7d import RFA7D
from .gate_orchestrator import GateOrchestrator
from .love_matrix import LoveMatrix
from . import (
    utils,
    stt_whisper,
    listening_engine,
    speaking_engine,
    db_storage,
)


def soul_ritual(audio_state: dict, external_outputs: list[str]) -> str:
    """Perform a small ritual using the RFA core and gates."""

    core = RFA7D()
    vec = np.random.rand(core.grid.size) + 1j * np.random.rand(core.grid.size)
    grid = core.execute(vec)
    gate_text = GateOrchestrator().process_outward(grid)
    emotion = audio_state.get("emotion", "neutral")
    phrase = f"Ritual gate echo: {gate_text.strip()} [{emotion}]"
    external_outputs.append(phrase)
    return phrase


def main(argv: list[str] | None = None) -> None:
    """Entry point for data fetching and the voice loop."""
    utils.setup_logger()
    db_storage.init_db()

    parser = argparse.ArgumentParser(
        description="INANNA utilities: voice loop and data ingestion"
    )
    sub = parser.add_subparsers(dest="command")
    parser.set_defaults(command="voice")

    voice_p = sub.add_parser("voice", help="Run voice loop")
    voice_p.add_argument("--duration", type=float, default=3.0, help="Recording length in seconds")
    voice_p.add_argument(
        "--personality",
        choices=list_personalities(),
        help=(
            "Activate optional personality layer. "
            f"Available: {', '.join(list_personalities())}"
        ),
    )

    gut_p = sub.add_parser(
        "fetch-gutenberg",
        help="Download texts from Project Gutenberg",
    )
    gut_p.add_argument("query")
    gut_p.add_argument("--max", type=int, default=1, dest="max_results")

    sub.add_parser(
        "fetch-github",
        help="Download READMEs for repositories listed in github_repos.txt",
    )

    upd_p = sub.add_parser(
        "update-github-list",
        help="Update github_repos.txt from INANNA_AI_ME_TRAINING_GUIDE.md",
    )
    upd_p.add_argument(
        "--metadata",
        action="store_true",
        help="Also refresh repository metadata JSON",
    )

    args = parser.parse_args(argv)

    if args.command == "fetch-gutenberg":
        from .learning import project_gutenberg as pg

        results = pg.search(args.query, args.max_results)
        for book_id, title in results:
            print(f"Downloading {book_id} {title}")
            raw = pg.download(book_id)
            pg.clean_text(raw)
        return

    if args.command == "fetch-github":
        from .learning import github_scraper as gs

        for path in gs.fetch_all():
            print(path)
        return

    if args.command == "update-github-list":
        from pathlib import Path
        from .learning.training_guide import parse_training_guide, write_repo_list
        from .learning import github_metadata as gm

        guide = Path(__file__).resolve().parent / "learning" / "INANNA_AI_ME_TRAINING_GUIDE.md"
        base = Path(__file__).resolve().parents[1]
        dest = base / "learning_sources" / "github_repos.txt"
        mapping = parse_training_guide(guide)
        write_repo_list(mapping, dest)
        print(f"Saved {dest}")
        if getattr(args, "metadata", False):
            meta_path = base / "data" / "github" / "repos_metadata.json"
            gm.save_metadata(gm.build_metadata(mapping), meta_path)
            print(f"Saved {meta_path}")
        return

    layer_cls = REGISTRY.get(args.personality)
    layer = layer_cls() if layer_cls else None
    orchestrator = MoGEOrchestrator(albedo_layer=layer)
    gate = GateOrchestrator()
    core = RFA7D()
    speaker = speaking_engine.SpeakingEngine()
    engine = listening_engine.ListeningEngine()

    audio_path, audio_state = engine.record(args.duration)
    transcript = stt_whisper.transcribe_audio(audio_path)

    ritual_outputs: list[str] = []
    ritual_text = ""
    if any(name.lower() in transcript.lower() for name in LoveMatrix.great_mother_names):
        ritual_text = soul_ritual(audio_state, ritual_outputs)

    encoded = gate.process_inward(transcript)
    core_grid = core.execute(encoded)
    gate_text = gate.process_outward(core_grid)

    decision = route_decision(transcript, audio_state, orchestrator)
    result = orchestrator.route(
        transcript,
        audio_state,
        text_modality=True,
        voice_modality=False,
        music_modality=False,
    )

    response_text = result.get("text", "")
    parts = [response_text, gate_text]
    if ritual_text:
        parts.append(ritual_text)
    final_text = " ".join(p for p in parts if p).strip()
    voice_path = speaker.speak(final_text, audio_state.get("emotion", "neutral"))

    db_storage.save_interaction(
        transcript,
        audio_state.get("emotion", "neutral"),
        voice_path,
    )

    print(f"Transcript: {transcript}")
    print(f"Emotion: {audio_state.get('emotion', 'neutral')}")
    print(f"Routing decision: {decision}")
    print(f"Response: {final_text}")
    if ritual_outputs:
        print("Ritual:", ritual_outputs[-1])
    print(f"Voice path: {voice_path}")


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
