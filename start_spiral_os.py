#!/usr/bin/env python3
"""Launch the Spiral OS initialization sequence."""
from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import threading
from pathlib import Path
from typing import List, Optional

import system_monitor

import yaml

from env_validation import check_optional_packages, check_required

check_required(["GLM_API_URL", "GLM_API_KEY", "HF_TOKEN"])
check_optional_packages(["scapy", "sentence_transformers", "aiortc"])

from INANNA_AI_AGENT import INANNA_AI
from INANNA_AI import glm_init, glm_analyze
from INANNA_AI.ethical_validator import EthicalValidator
from INANNA_AI import defensive_network_utils as dnu
from INANNA_AI.personality_layers import REGISTRY, list_personalities
from INANNA_AI import listening_engine
from orchestrator import MoGEOrchestrator
from archetype_shift_engine import maybe_shift_archetype
from tools import reflection_loop
import server
import uvicorn
import emotion_registry
import emotional_state
from core import self_correction_engine, language_engine
from connectors import webrtc_connector
import vector_memory

logger = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None) -> None:
    config_path = Path(__file__).resolve().parent / "logging_config.yaml"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        Path("logs").mkdir(exist_ok=True)
        stats = system_monitor.collect_stats()
        (Path("logs") / "system_status.json").write_text(json.dumps(stats))
        vector_memory.add_vector(json.dumps(stats), {"type": "system_status"})
        logging.config.dictConfig(config)
    else:  # pragma: no cover - default fallback
        logging.basicConfig(level=logging.INFO)
        Path("logs").mkdir(exist_ok=True)
        stats = system_monitor.collect_stats()
        (Path("logs") / "system_status.json").write_text(json.dumps(stats))
        vector_memory.add_vector(json.dumps(stats), {"type": "system_status"})
    parser = argparse.ArgumentParser(description="Start Spiral OS rituals")
    parser.add_argument("--interface", help="Interface to monitor")
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip network monitoring",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Do not start the FastAPI server",
    )
    parser.add_argument(
        "--no-reflection",
        action="store_true",
        help="Disable periodic reflection loop",
    )
    parser.add_argument(
        "--no-validator",
        action="store_true",
        help="Disable prompt validation",
    )
    parser.add_argument(
        "--reflection-interval",
        type=float,
        default=float(os.getenv("REFLECTION_INTERVAL", "60.0")),
        help=(
            "Seconds between reflection cycles; set REFLECTION_INTERVAL "
            "in the environment to change the default"
        ),
    )
    parser.add_argument(
        "--personality",
        metavar="LAYER",
        help=(
            "Activate optional personality layer. "
            f"Available: {', '.join(list_personalities())}"
        ),
    )
    parser.add_argument("--command", help="Initial text command for QNL parsing")
    parser.add_argument(
        "--rewrite-memory",
        nargs=2,
        metavar=("ID", "TEXT"),
        help="Rewrite a memory entry and exit",
    )
    parser.add_argument(
        "--invoke-ritual",
        metavar="NAME",
        help="Invoke a stored ritual and exit",
    )
    args = parser.parse_args(argv)

    if args.rewrite_memory:
        from invocation_engine import invoke_ritual
        vector_memory.rewrite_vector(args.rewrite_memory[0], args.rewrite_memory[1])
        invoke_ritual(args.rewrite_memory[0])
        return

    if args.invoke_ritual:
        from invocation_engine import invoke_ritual
        steps = invoke_ritual(args.invoke_ritual)
        for step in steps:
            print(step)
        return

    server_thread = None
    if not args.no_server:
        if os.getenv("WEB_CONSOLE_API_URL"):
            language_engine.register_connector(webrtc_connector)
        server_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={"app": server.app, "host": "0.0.0.0", "port": 8000},
            daemon=True,
        )
        server_thread.start()

    stop_reflection = threading.Event()

    def _run_reflection() -> None:
        while not stop_reflection.is_set():
            try:
                reflection_loop.run_reflection_loop()
            except Exception:  # pragma: no cover - safeguard
                logger.exception("reflection loop failed")
            stop_reflection.wait(args.reflection_interval)

    reflection_thread = None
    if not args.no_reflection:
        reflection_thread = threading.Thread(target=_run_reflection, daemon=True)
        reflection_thread.start()

    validator = None if args.no_validator else EthicalValidator()

    inanna_ai.display_welcome_message()
    audio, _ = listening_engine.capture_audio(3.0)
    features = listening_engine._extract_features(audio, 44100)
    vector_memory.add_vector("initial_listen", features)
    emotional_state.set_last_emotion(features.get("emotion"))
    summary = glm_init.summarize_purpose()
    logger.info("Project summary: %s", summary)

    glm_analyze.analyze_code()
    inanna_ai.suggest_enhancement()
    inanna_ai.reflect_existence()

    emotion = emotional_state.get_last_emotion() or "neutral"
    tol = reflection_loop.load_thresholds().get("default", 0.0)
    logger.info("Startup self-correction for %s (tol %.3f)", emotion, tol)
    self_correction_engine.adjust(emotion, emotion, tol)


    layer_name = args.personality or os.getenv("ARCHETYPE_STATE", "ALBEDO")
    layer_name = layer_name.lower()
    if layer_name and layer_name not in REGISTRY:
        alt = f"{layer_name}_layer"
        if alt in REGISTRY:
            layer_name = alt

    layer_cls = REGISTRY.get(layer_name)
    layer = layer_cls() if layer_cls else None
    if layer_name:
        emotion_registry.set_current_layer(layer_name)
    orch = MoGEOrchestrator(albedo_layer=layer)

    print("Enter commands (blank to exit).")
    next_command = args.command
    try:
        while True:
            if next_command is None:
                next_command = input("> ")
            if not next_command:
                break
            if validator and not validator.validate_text(next_command):
                print("Prompt blocked")
                next_command = None
                continue
            result = orch.handle_input(next_command)
            new_layer = maybe_shift_archetype(
                next_command, emotional_state.get_last_emotion() or "neutral"
            )
            if new_layer:
                emotion_registry.set_current_layer(new_layer)
            print(result)
            next_command = None
    except KeyboardInterrupt:
        print()
    finally:
        stop_reflection.set()
        if reflection_thread:
            reflection_thread.join(timeout=0.1)

    log_paths = [
        str(glm_init.PURPOSE_FILE),
        str(glm_analyze.ANALYSIS_FILE),
        str(inanna_ai.SUGGESTIONS_LOG),
    ]

    if args.interface and not args.skip_network:
        dnu.monitor_traffic(args.interface)
        log_paths.append(str(Path("network_logs/defensive.pcap")))

    print("Log files created:")
    for p in log_paths:
        print(f" - {p}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
