# -*- coding: utf-8 -*-
"""Multimodal Generative Expression orchestrator.

This module exposes :class:`MoGEOrchestrator`, the central router that
directs textual and audio input to the appropriate language or synthesis
models.  Routing decisions take the current emotional context, task
classification and recent interaction history into account.  Model weights
are updated over time based on benchmark results to favour better performing
systems.  The :mod:`soundfile` dependency is optional; if it is not available,
audio export falls back to the built-in :mod:`wave` module.
"""

from __future__ import annotations

import logging
import tempfile
import threading
import wave as wave_module
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Deque, Dict, List

import hashlib

try:
    import soundfile as sf  # pragma: no cover
except Exception:
    sf = None  # pragma: no cover

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore
try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

import archetype_shift_engine
import crown_decider
import emotional_state
import learning_mutator
import training_guide
from audio import voice_aura
from core import context_tracker, language_engine, task_parser
from core.emotion_analyzer import EmotionAnalyzer
from core.memory_logger import MemoryLogger
from core.model_selector import ModelSelector
from core.task_profiler import TaskProfiler
from corpus_memory_logging import load_interactions, log_interaction, log_ritual_result
from crown_config import settings
from INANNA_AI import listening_engine, response_manager, voice_layer_albedo
from INANNA_AI.personality_layers import REGISTRY as PERSONALITY_REGISTRY
from INANNA_AI.personality_layers import AlbedoPersonality
from insight_compiler import load_insights, update_insights
from SPIRAL_OS import qnl_engine, symbolic_parser
from task_profiling import ritual_action_sequence
from tools import reflection_loop

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except Exception:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import invocation_engine as _invocation_engine
except Exception:  # pragma: no cover - optional dependency
    _invocation_engine = None  # type: ignore[assignment]

vector_memory = _vector_memory
# Optional vector memory subsystem; ``None`` if unavailable.
invocation_engine = _invocation_engine
# Optional invocation engine subsystem; ``None`` if unavailable.

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VersionInfo:
    """Semantic version information for :mod:`rag.orchestrator`."""

    major: int
    minor: int
    patch: int


__version__ = VersionInfo(0, 1, 0)


class MoGEOrchestrator:
    """High level controller for routing user input.

    ``MoGEOrchestrator`` analyses the supplied text, determines the dominant
    emotion and task type and then selects a language model accordingly.  It
    maintains a short history of previous interactions, uses vector memory to
    refine model weights and can optionally produce voice or music output.  The
    :py:meth:`route` method implements the main decision logic while
    :py:meth:`handle_input` parses Quantum Narrative Language before routing.
    """

    def __init__(
        self,
        *,
        albedo_layer: AlbedoPersonality | None = None,
        db_path: Path | None = None,
        emotion_analyzer: EmotionAnalyzer | None = None,
        model_selector: ModelSelector | None = None,
        memory_logger: MemoryLogger | None = None,
        task_profiler: TaskProfiler | None = None,
    ) -> None:
        self._responder = response_manager.ResponseManager()
        self._albedo = albedo_layer
        self._active_layer_name: str | None = None
        self._context: Deque[Dict[str, Any]] = deque(maxlen=5)
        if SentenceTransformer is not None:
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        else:  # pragma: no cover - fallback when dependency missing
            self._embedder = None
        self._model_selector = model_selector or ModelSelector(db_path=db_path)
        self._emotion_analyzer = emotion_analyzer or EmotionAnalyzer()
        self._memory_logger = memory_logger or MemoryLogger()
        self._memory_logger.log_interaction = log_interaction
        self._memory_logger.load_interactions = load_interactions
        self._memory_logger.log_ritual_result = log_ritual_result
        self._task_profiler = task_profiler or TaskProfiler()
        self.mood_state = self._emotion_analyzer.mood_state
        self._interaction_count = 0
        self._invocation_engine = invocation_engine

    @staticmethod
    def _select_plane(weight: float, archetype: str) -> str:
        """Return ``ascension`` or ``underworld`` based on ``weight`` and
        ``archetype``.
        """
        if weight >= 0.6 or archetype.lower() in {"hero", "sage", "jester"}:
            return "ascension"
        return "underworld"

    def route(
        self,
        text: str,
        emotion_data: Dict[str, Any],
        *,
        qnl_data: Dict[str, Any] | None = None,
        text_modality: bool = True,
        voice_modality: bool = False,
        music_modality: bool = False,
        documents: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        """Process ``text`` with models based on ``emotion_data`` and flags."""
        emotion = emotion_data.get("emotion", "neutral")
        if "archetype" not in emotion_data or "weight" not in emotion_data:
            enriched = self._emotion_analyzer.analyze(emotion)
            emotion_data = {**emotion_data, **enriched}
            emotion = emotion_data["emotion"]
        archetype = emotion_data["archetype"]
        weight = emotion_data["weight"]
        plane = self._select_plane(weight, archetype)

        tone = None
        intents = None
        if qnl_data is not None:
            tone = qnl_data.get("tone")
            intents = symbolic_parser.parse_intent(qnl_data)

        layer_name = emotional_state.get_current_layer()
        if layer_name:
            layer_cls = PERSONALITY_REGISTRY.get(layer_name)
            if layer_cls is not None and not isinstance(self._albedo, layer_cls):
                self._albedo = layer_cls()
            self._active_layer_name = layer_name
        else:
            # derive currently active layer from the instance if present
            self._active_layer_name = None
            if self._albedo is not None:
                for name, cls in PERSONALITY_REGISTRY.items():
                    if isinstance(self._albedo, cls):
                        self._active_layer_name = name
                        break

        task = self._task_profiler.classify(text)
        history_tasks = [c["task"] for c in self._context]

        model = self._model_selector.select_model(task, emotion, weight, history_tasks)

        start = perf_counter()
        result: Dict[str, Any] = {
            "plane": plane,
            "archetype": archetype,
            "weight": weight,
            "model": model,
        }
        if vector_memory is not None:
            vector_memory.add_vector(
                text,
                {
                    "type": "routing_decision",
                    "selected_model": model,
                    "emotion": emotion,
                },
            )
        if intents is not None:
            result["qnl_intents"] = intents

        if text_modality:
            try:
                if self._albedo is not None:
                    result["text"] = self._albedo.generate_response(text)
                else:
                    result["text"] = self._responder.generate_reply(text, emotion_data)
            except Exception:  # pragma: no cover - safeguard
                logger.exception("model %s failed, falling back to GLM", model)
                result["model"] = "glm"
                result["text"] = self._responder.generate_reply(text, emotion_data)

        if voice_modality:
            opts = crown_decider.decide_expression_options(emotion)
            settings.crown_tts_backend = (
                opts.get("tts_backend") or settings.crown_tts_backend
            )
            result.update(
                {
                    "tts_backend": opts.get("tts_backend"),
                    "avatar_style": opts.get("avatar_style"),
                    "aura_amount": opts.get("aura_amount"),
                }
            )
            if vector_memory is not None:
                vector_memory.add_vector(
                    text,
                    {
                        "type": "expression_decision",
                        "tts_backend": opts.get("tts_backend"),
                        "avatar_style": opts.get("avatar_style"),
                        "aura_amount": opts.get("aura_amount"),
                        "emotion": emotion,
                        "soul_state": opts.get("soul_state"),
                    },
                )

            speech_input = result.get("text", text)
            if tone is not None:
                path = voice_layer_albedo.modulate_voice(speech_input, tone)
            else:
                path = language_engine.synthesize_speech(speech_input, emotion)
            result["voice_path"] = str(
                voice_aura.apply_voice_aura(
                    Path(path), emotion=emotion, amount=opts.get("aura_amount", 0.5)
                )
            )

        if music_modality and np is not None:
            hex_input = text.encode("utf-8").hex()
            phrases, wave = qnl_engine.hex_to_song(hex_input, duration_per_byte=0.05)
            digest = hashlib.sha256(hex_input.encode("utf-8")).hexdigest()[:8]
            wav_path = Path(tempfile.gettempdir()) / f"qnl_{digest}.wav"
            if sf is None:
                wav_data = np.clip(wave, -1.0, 1.0)
                wav_data = (wav_data * 32767).astype(np.int16)
                with wave_module.open(str(wav_path), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    wf.writeframes(wav_data.tobytes())
            else:
                sf.write(wav_path, wave, 44100)
            result["music_path"] = str(wav_path)
            result["qnl_phrases"] = phrases
        elif music_modality:
            logger.warning("NumPy not available; music generation skipped")

        # Update lightweight context memory
        if self._embedder is not None and np is not None:
            emb = np.asarray(self._embedder.encode([text]))[0]
        elif np is not None:
            emb = np.array([len(text)], dtype=float)
        else:
            emb = [float(len(text))]
        self._context.append({"text": text, "task": task, "embedding": emb})

        elapsed = perf_counter() - start
        if text_modality and "text" in result:
            self._model_selector.benchmark(model, text, result["text"], elapsed)

        self._interaction_count += 1
        self._memory_logger.log_interaction(
            text, {"intents": intents or []}, result, "ok"
        )

        if self._interaction_count % 20 == 0:
            entries = self._memory_logger.load_interactions()
            update_insights(entries)
            suggestions = learning_mutator.propose_mutations(load_insights())
            if suggestions:
                result["suggestions"] = suggestions
                for s in suggestions:
                    # structured logging instead of printing to stdout
                    logger.info({"suggestion": s})

        return result

    def handle_input(self, text: str) -> Dict[str, Any]:
        """Parse ``text`` as QNL, update mood and delegate to :meth:`route`."""
        # Detect simple command phrases
        for intent in task_parser.parse(text):
            action = intent.get("action")
            if action == "show_avatar":
                context_tracker.state.avatar_loaded = True
                emotion = emotional_state.get_last_emotion() or "neutral"
                opts = crown_decider.decide_expression_options(emotion)
                self._memory_logger.log_interaction(
                    text,
                    {"action": "show_avatar"},
                    {
                        "message": "avatar displayed",
                        "avatar_style": opts.get("avatar_style"),
                        "aura_amount": opts.get("aura_amount"),
                    },
                    "ok",
                )
            if action == "start_call":
                context_tracker.state.in_call = True

        qnl_data = qnl_engine.parse_input(text)
        results = symbolic_parser.parse_intent(qnl_data)
        gathered = symbolic_parser._gather_text(qnl_data).lower()
        intents: List[Dict[str, Any]] = []
        for name, info in symbolic_parser._INTENTS.items():
            triggers = [name] + info.get("synonyms", []) + info.get("glyphs", [])
            if any(t.lower() in gathered for t in triggers):
                intent = {"intent": name, "action": info.get("action")}
                intent.update(qnl_data)
                intents.append(intent)
        for intent, res in zip(intents, results):
            success = not (
                isinstance(res, dict) and res.get("status") in {"unhandled", "todo"}
            )
            training_guide.log_result(intent, success, qnl_data.get("tone"), res)
        emotion = qnl_data.get("tone", "neutral")
        emotion_data = self._emotion_analyzer.analyze(emotion)
        dominant = emotion_data["emotion"]

        try:
            thresholds = reflection_loop.load_thresholds()
        except Exception:
            thresholds = {"default": 1.0}
        intensity = self.mood_state[dominant]
        limit = thresholds.get(dominant, thresholds.get("default", 1.0))
        if intensity > limit:
            layer = archetype_shift_engine.EMOTION_LAYER_MAP.get(dominant)
            current = emotional_state.get_current_layer()
            if layer and layer != current:
                emotional_state.set_current_layer(layer)

        tasks: List[str]
        if self._invocation_engine is not None:
            try:
                symbols = self._invocation_engine._extract_symbols(text)
                tasks = ritual_action_sequence(symbols, dominant)
                for res in self._invocation_engine.invoke(
                    f"{symbols} [{dominant}]", self
                ):
                    if isinstance(res, list):
                        tasks.extend(res)
            except Exception:  # pragma: no cover - safeguard
                logger.exception("invocation engine failed; using default ritual")
                tasks = ritual_action_sequence("", dominant)
        else:
            logger.info("invocation engine unavailable; skipping ritual invocation")
            tasks = ritual_action_sequence("", dominant)

        for act in tasks:
            symbolic_parser.parse_intent({"text": act, "tone": dominant})

        result = self.route(text, emotion_data, qnl_data=qnl_data)
        if self._active_layer_name:
            emotional_state.set_current_layer(self._active_layer_name)
        if context_tracker.state.avatar_loaded:
            try:
                reflection_loop.run_reflection_loop(iterations=1)
            except Exception:  # pragma: no cover - safeguard
                logger.exception("reflection loop failed")

        try:
            _, state = listening_engine.analyze_audio(0.5)
            meaning = state.get("silence_meaning", "")
            if "Extended" in meaning and self._invocation_engine is not None:
                steps = self._invocation_engine.invoke_ritual("silence_introspection")
                self._memory_logger.log_ritual_result("silence_introspection", steps)
        except Exception:  # pragma: no cover - safeguard
            logger.exception("silence introspection failed; skipping ritual")
            self._memory_logger.log_ritual_result("silence_introspection", [])

        return result


def schedule_action(func: Callable[[], Any], delay: float) -> threading.Timer:
    """Execute ``func`` after ``delay`` seconds using a timer."""
    timer = threading.Timer(delay, func)
    timer.start()
    return timer


__all__ = [
    "MoGEOrchestrator",
    "schedule_action",
]
if vector_memory is not None:
    __all__.append("vector_memory")
if invocation_engine is not None:
    __all__.append("invocation_engine")
