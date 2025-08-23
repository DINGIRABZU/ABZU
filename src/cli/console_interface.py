from __future__ import annotations

"""Interactive REPL for the Crown agent."""

import argparse
import logging
import os
import subprocess
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
from rag.orchestrator import MoGEOrchestrator
from tools import sandbox_session, session_logger, virtual_env_manager

try:
    from crown_prompt_orchestrator import crown_prompt_orchestrator
except Exception:  # pragma: no cover - orchestrator may be added later
    crown_prompt_orchestrator = None

logger = logging.getLogger(__name__)

HISTORY_FILE = Path("data/console_history.txt")


def _send_audio_path(path: Path) -> None:
    """Notify the video stream service of new audio."""

    url = os.getenv("VIDEO_STREAM_URL", "http://localhost:8000")
    try:
        requests.post(
            f"{url.rstrip('/')}/avatar-audio",
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
            print(
                f"[{attempt}/{retries}] Unable to reach GLM service at {health_url}: {exc}\n"
                "Start the model server with 'bash crown_model_launcher.sh' and ensure "
                "the GLM_API_URL environment variable points to the correct endpoint."
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

    def _play_music(prompt: str) -> None:
        """Generate and play music for ``prompt``."""
        try:
            result = orch.route(
                prompt,
                {},
                text_modality=False,
                voice_modality=False,
                music_modality=True,
            )
            music_path = result.get("music_path")
            if not music_path:
                print("No music generated.")
                return
            session_logger.log_audio(Path(music_path))
            try:
                speaking_engine.play_wav(music_path)
            except Exception:  # pragma: no cover - playback may fail
                logger.exception("music playback failed")
            print(f"Music saved to {music_path}")
        except Exception:  # pragma: no cover - generation may fail
            logger.exception("music generation failed")
            print("Music generation failed")

    if args.music:
        _play_music(args.music)
        return

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
            if command.startswith("/memory"):
                _, _, q = command.partition(" ")
                _show_memory(q)
                continue
            if command.startswith("/music"):
                _, _, music_prompt = command.partition(" ")
                if music_prompt:
                    _play_music(music_prompt)
                else:
                    print("Usage: /music <prompt>")
                continue
            if command.startswith("/clone-voice"):
                _, _, sample_text = command.partition(" ")
                try:
                    voice_clone = voice_cloner.VoiceCloner()
                    sample_path = Path("data/voice_sample.wav")
                    out_path = Path("data/voice_clone.wav")
                    voice_clone.capture_sample(sample_path)
                    voice_clone.synthesize(
                        sample_text or "Voice clone ready.", out_path
                    )
                    speaking_engine.play_wav(str(out_path))
                    print("Cloned voice registered for future replies.")
                except Exception as exc:
                    print(f"Voice cloning unavailable: {exc}")
                    voice_clone = None
                continue
            if command.startswith("/sandbox"):
                _, _, patch_path_str = command.partition(" ")
                if not patch_path_str:
                    print("Usage: /sandbox <patch-file>")
                    continue
                patch_file = Path(patch_path_str)
                try:
                    patch_text = patch_file.read_text()
                except Exception as exc:
                    print(f"Unable to read patch file: {exc}")
                    continue
                repo_root = Path(__file__).resolve().parents[1]
                try:
                    sandbox_root = sandbox_session.create_sandbox(
                        repo_root, virtual_env_manager
                    )
                    sandbox_session.apply_patch(sandbox_root, patch_text)
                    env = sandbox_root / ".venv"
                    req_file = sandbox_root / "tests" / "requirements.txt"
                    virtual_env_manager.install_requirements(env, req_file)
                    try:
                        result = virtual_env_manager.run(
                            env, ["pytest"], cwd=sandbox_root
                        )
                        print(result.stdout)
                        print("Sandbox tests passed.")
                    except subprocess.CalledProcessError as exc:
                        print(exc.stdout)
                        print(exc.stderr)
                        print("Sandbox tests failed.")
                except Exception as exc:
                    print(f"Sandbox error: {exc}")
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
    except Exception as exc:  # pragma: no cover - optional deps
        logger.error("Failed to load memory: %s", exc)
        print("Memory unavailable")


__all__ = ["run_repl"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    run_repl()
