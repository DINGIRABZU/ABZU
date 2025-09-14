"""Interactive REPL for the Crown agent."""

from __future__ import annotations

import argparse
import logging
import os
import time
from pathlib import Path

import requests  # type: ignore[import-untyped]
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

import emotional_state
from audio import voice_cloner
from core import avatar_expression_engine, context_tracker
from INANNA_AI import speaking_engine
from INANNA_AI.glm_integration import GLMIntegration
from init_crown_agent import initialize_crown
from memory.search import query_all
from neoabzu_rag import MoGEOrchestrator
from tools import session_logger
from bana import narrative as bana_narrative
import servant_model_manager as smm
from .music_helper import play_music
from .sandbox_helper import run_sandbox
from .voice_clone_helper import clone_voice

try:
    from crown_prompt_orchestrator import crown_prompt_orchestrator
except Exception:  # pragma: no cover - orchestrator may be added later
    crown_prompt_orchestrator = None

logger = logging.getLogger(__name__)

HISTORY_FILE = Path("data/console_history.txt")


def _send_audio_path(path: Path) -> None:
    """Notify the video stream service of new audio."""

    url = os.getenv("VIDEO_STREAM_URL", "http://localhost:8000")
    agent = os.getenv("VIDEO_STREAM_AGENT", "agent")
    try:
        requests.post(
            f"{url.rstrip('/')}/{agent}/avatar-audio",
            json={"path": str(path)},
            timeout=5,
        )
    except Exception:  # pragma: no cover - network issues
        logger.exception("failed to send audio path")


def _wait_for_glm_ready(retries: int = 3, delay: float = 5.0) -> GLMIntegration:
    """Return a ``GLMIntegration`` once the service is reachable.

    Offers actionable guidance when the health endpoint cannot be contacted.
    """
    endpoint = os.getenv("GLM_API_URL", "http://localhost:8000")
    health_url = endpoint.rstrip("/") + "/health"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(health_url, timeout=5)
            resp.raise_for_status()
            return initialize_crown()
        except (requests.RequestException, SystemExit) as exc:
            logger.error(
                "[%s/%s] Unable to reach GLM service at %s: %s\n"
                "Start the model server with 'bash crown_model_launcher.sh' and ensure "
                "the GLM_API_URL environment variable points to the correct endpoint.",
                attempt,
                retries,
                health_url,
                exc,
            )
        if attempt < retries:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    print(
        f"GLM service is still unreachable after {retries} attempts. "
        "Please start the server and try again."
    )
    raise SystemExit(1)


def run_repl(argv: list[str] | None = None) -> None:
    """Start the interactive console."""
    parser = argparse.ArgumentParser(description="Crown agent console")
    parser.add_argument(
        "--speak",
        action="store_true",
        help="Synthesize replies using the speaking engine",
    )
    parser.add_argument(
        "--music",
        metavar="PROMPT",
        help="Generate a music track for the given prompt and exit",
    )
    args = parser.parse_args(argv)

    print("Waiting for GLM service to become available...")
    try:
        glm = _wait_for_glm_ready()
    except SystemExit:
        return
    orch = MoGEOrchestrator()
    speak = args.speak
    voice_clone: voice_cloner.VoiceCloner | None = None

    if args.music:
        play_music(orch, args.music)
        return

    session = PromptSession(history=FileHistory(str(HISTORY_FILE)))
    print("Crown console started. Type /exit to quit.")

    while True:
        try:
            with patch_stdout():
                text = session.prompt("crown> ")
        except (EOFError, KeyboardInterrupt):
            logger.error("console input interrupted")
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
            if command.startswith("/memory"):
                _, _, q = command.partition(" ")
                _show_memory(q)
                continue
            if command.startswith("/music"):
                _, _, music_prompt = command.partition(" ")
                play_music(orch, music_prompt)
                continue
            if command.startswith("/clone-voice"):
                _, _, sample_text = command.partition(" ")
                voice_clone = clone_voice(sample_text)
                continue
            if command.startswith("/sandbox"):
                _, _, patch_path_str = command.partition(" ")
                run_sandbox(patch_path_str)
                continue
            print(f"Unknown command: {command}")
            continue

        if crown_prompt_orchestrator is None:
            print("Orchestrator unavailable")
            continue
        try:
            reply = crown_prompt_orchestrator(command, glm)
        except Exception:  # pragma: no cover - runtime errors
            logger.exception("Error: could not process input")
            continue
        print(reply)
        if isinstance(reply, dict):
            model = str(reply.get("model", ""))
            pulse = smm.pulse_metrics(model)
            print(
                f"[routing] model={model} latency={pulse['avg_latency']:.3f}s "
                f"fail={pulse['failure_rate']:.2%}"
            )
            try:
                event = bana_narrative.emit(
                    "operator", "console_command", {"command": command, "model": model}
                )
                print(f"[narrative] {event['event_type']} {event['payload']}")
            except Exception:
                logger.exception("narrative emit failed")
        if speak and isinstance(reply, dict):
            text_reply = reply.get("text", str(reply))
            emotion = reply.get("emotion", "neutral")
            try:
                voice_path: str | None
                if voice_clone is not None:
                    out_path = Path("data/cloned_reply.wav")
                    voice_path = str(
                        voice_clone.synthesize(text_reply, out_path, emotion)
                    )
                else:
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
                    _send_audio_path(Path(voice_path))
                    speaking_engine.play_wav(voice_path)
                    frames = []
                    if context_tracker.state.avatar_loaded:
                        for frame in avatar_expression_engine.stream_avatar_audio(
                            Path(voice_path)
                        ):
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


def _show_memory(query: str = "") -> None:
    """Display unified memory search results."""
    try:
        entries = query_all(query)
        if not entries:
            print("No memory entries found.")
            return
        for e in entries:
            ts = e.get("timestamp", "")
            text = e.get("text", "")
            src = e.get("source", "")
            if ts:
                print(f"{ts} [{src}] {text}")
            else:
                print(f"[{src}] {text}")
    except Exception:  # pragma: no cover - optional deps
        logger.exception("Memory unavailable")


__all__ = ["run_repl"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    run_repl()
