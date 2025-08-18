from __future__ import annotations

"""Interactive REPL for the Crown agent."""

import argparse
import logging
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

from init_crown_agent import initialize_crown
from orchestrator import MoGEOrchestrator
from core import context_tracker, avatar_expression_engine
from INANNA_AI import speaking_engine
from tools import session_logger
import emotional_state

try:
    from crown_prompt_orchestrator import crown_prompt_orchestrator
except Exception:  # pragma: no cover - orchestrator may be added later
    crown_prompt_orchestrator = None  # type: ignore

logger = logging.getLogger(__name__)

HISTORY_FILE = Path("data/console_history.txt")


def run_repl(argv: list[str] | None = None) -> None:
    """Start the interactive console."""
    parser = argparse.ArgumentParser(description="Crown agent console")
    parser.add_argument(
        "--speak",
        action="store_true",
        help="Synthesize replies using the speaking engine",
    )
    args = parser.parse_args(argv)

    glm = initialize_crown()
    orch = MoGEOrchestrator()
    speak = args.speak
    session = PromptSession(history=FileHistory(str(HISTORY_FILE)))
    print("Crown console started. Type /exit to quit.")

    while True:
        try:
            with patch_stdout():
                text = session.prompt("crown> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        command = text.strip()
        if command.startswith("/"):
            if command == "/exit":
                break
            if command == "/reload":
                glm = initialize_crown()
                print("Agent reloaded.")
                continue
            if command == "/memory":
                _show_memory()
                continue
            print(f"Unknown command: {command}")
            continue

        if crown_prompt_orchestrator is None:
            print("Orchestrator unavailable")
            continue
        try:
            reply = crown_prompt_orchestrator(command, glm)
        except Exception as exc:  # pragma: no cover - runtime errors
            logger.error("orchestrator failed: %s", exc)
            print("Error: could not process input")
            continue
        print(reply)
        if speak and isinstance(reply, dict):
            text_reply = reply.get("text", str(reply))
            emotion = reply.get("emotion", "neutral")
            try:
                result = orch.route(
                    text_reply,
                    {"emotion": emotion},
                    text_modality=False,
                    voice_modality=True,
                    music_modality=False,
                )
                voice_path = result.get("voice_path")
                if voice_path:
                    session_logger.log_audio(Path(voice_path))
                    speaking_engine.play_wav(voice_path)
                    frames = []
                    if context_tracker.state.avatar_loaded:
                        for frame in avatar_expression_engine.stream_avatar_audio(Path(voice_path)):
                            frames.append(frame)
                    if frames:
                        session_logger.log_video(frames)
                    try:
                        from INANNA_AI import speech_loopback_reflector as slr

                        info = slr.reflect(voice_path)
                        emotional_state.set_last_emotion(info.get("emotion"))
                        # Reflection informs emotional tone for next reply
                    except Exception:  # pragma: no cover - optional deps
                        logger.exception("speech reflection failed")
            except Exception:  # pragma: no cover - synthesis may fail
                logger.exception("speaking failed")


def _show_memory() -> None:
    """Display recent interaction logs."""
    try:
        from corpus_memory_logging import load_interactions

        entries = load_interactions(limit=5)
        if not entries:
            print("No memory entries found.")
            return
        for e in entries:
            ts = e.get("timestamp", "")
            text = e.get("input", "")
            print(f"{ts}: {text}")
    except Exception as exc:  # pragma: no cover - optional deps
        logger.error("Failed to load memory: %s", exc)
        print("Memory unavailable")


__all__ = ["run_repl"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    run_repl()
