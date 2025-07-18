# -*- coding: utf-8 -*-
"""Multimodal Generative Expression orchestrator.

This module exposes :class:`MoGEOrchestrator`, the central router that
directs textual and audio input to the appropriate language or synthesis
models.  Routing decisions take the current emotional context, task
classification and recent interaction history into account.  Model weights
are updated over time based on benchmark results to favour better performing
systems.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any, Dict, Deque, List, Callable
import os
from collections import deque
import soundfile as sf
from time import perf_counter
import threading
import logging

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

import numpy as np

from task_profiling import classify_task, ritual_action_sequence

from INANNA_AI import response_manager, emotion_analysis, db_storage
from INANNA_AI.personality_layers import (
    AlbedoPersonality,
    REGISTRY as PERSONALITY_REGISTRY,
)
from INANNA_AI import voice_layer_albedo
import crown_decider
import voice_aura
from core import task_parser, context_tracker, language_engine
from SPIRAL_OS import qnl_engine, symbolic_parser
import invocation_engine
import emotional_state
import training_guide
from corpus_memory_logging import (
    log_interaction,
    load_interactions,
    log_ritual_result,
)
from insight_compiler import update_insights, load_insights
import learning_mutator
from tools import reflection_loop
from INANNA_AI import listening_engine
import vector_memory
import archetype_shift_engine

# Emotion to model lookup derived from docs/crown_manifest.md
_EMOTION_MODEL_MATRIX = {
    "joy": "deepseek",
    "excited": "deepseek",
    "stress": "mistral",
    "fear": "mistral",
    "sad": "mistral",
    "calm": "glm",
    "neutral": "glm",
}

logger = logging.getLogger(__name__)


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
    ) -> None:
        self._responder = response_manager.ResponseManager()
        self._albedo = albedo_layer
        self._active_layer_name: str | None = None
        self._context: Deque[Dict[str, Any]] = deque(maxlen=5)
        if SentenceTransformer is not None:
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        else:  # pragma: no cover - fallback when dependency missing
            self._embedder = None
        self._model_weights = {"glm": 1.0, "deepseek": 1.0, "mistral": 1.0}
        self._alpha = 0.1
        self._db_path = db_path or db_storage.DB_PATH
        db_storage.init_db(self._db_path)
        self._mood_alpha = 0.2
        self.mood_state: Dict[str, float] = {
            e: (1.0 if e == "neutral" else 0.0)
            for e in emotion_analysis.EMOTION_WEIGHT
        }
        self._interaction_count = 0
        self._invocation_engine = invocation_engine

    @staticmethod
    def _select_plane(weight: float, archetype: str) -> str:
        """Return ``ascension`` or ``underworld`` based on ``weight`` and ``archetype``."""
        if weight >= 0.6 or archetype.lower() in {"hero", "sage", "jester"}:
            return "ascension"
        return "underworld"

    @staticmethod
    def _coherence(text: str) -> float:
        """Return a simple coherence score for ``text``."""
        words = text.split()
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    @staticmethod
    def _relevance(source: str, generated: str) -> float:
        """Return a Jaccard similarity between ``source`` and ``generated``."""
        src = set(source.split())
        gen = set(generated.split())
        if not src or not gen:
            return 0.0
        return len(src & gen) / len(src | gen)

    def _update_weights(self, model: str, rt: float, coh: float, rel: float) -> None:
        reward = coh + rel - 0.1 * rt
        current = self._model_weights.get(model, 1.0)
        self._model_weights[model] = (1 - self._alpha) * current + self._alpha * reward

    def _update_mood(self, emotion: str) -> None:
        """Update ``mood_state`` using an exponential moving average."""
        for key in list(self.mood_state):
            target = 1.0 if key.lower() == emotion.lower() else 0.0
            self.mood_state[key] = (1 - self._mood_alpha) * self.mood_state.get(key, 0.0) + self._mood_alpha * target

    def _benchmark(self, model: str, prompt: str, output: str, elapsed: float) -> None:
        coh = self._coherence(output)
        rel = self._relevance(prompt, output)
        db_storage.log_benchmark(model, elapsed, coh, rel, db_path=self._db_path)
        self._update_weights(model, elapsed, coh, rel)

    @staticmethod
    def _model_from_emotion(emotion: str) -> str:
        """Return preferred model for the given emotion."""
        return _EMOTION_MODEL_MATRIX.get(emotion.lower(), "glm")

    def _choose_model(
        self,
        task: str,
        weight: float,
        history: List[str],
        *,
        weights: Dict[str, float] | None = None,
    ) -> str:
        """Return LLM name based on task, ``weight`` and ``history``."""
        emotional_ratio = 0.0
        if history:
            emotional_ratio = history.count("emotional") / len(history)

        base = {"glm": 0.0, "deepseek": 0.0, "mistral": 0.0}

        if weight > 0.8 or emotional_ratio > 0.5 or task == "philosophical":
            base["mistral"] = 1.0
        if task == "instructional":
            base["deepseek"] = 1.0
        if not any(base.values()):
            base["glm"] = 1.0

        effective = weights or self._model_weights
        scores = {m: base[m] * effective.get(m, 1.0) for m in base}
        return max(scores, key=scores.get)

    def route(
        self,
        text: str,
        emotion_data: Dict[str, Any],
        *,
        qnl_data: Dict[str, Any] | None = None,
        text_modality: bool = True,
        voice_modality: bool = False,
        music_modality: bool = False,
    ) -> Dict[str, Any]:
        """Process ``text`` with models based on ``emotion_data`` and flags."""
        emotion = emotion_data.get("emotion", "neutral")
        archetype = emotion_data.get("archetype") or emotion_analysis.emotion_to_archetype(emotion)
        weight = emotion_data.get("weight")
        if weight is None:
            weight = emotion_analysis.emotion_weight(emotion)
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

        task = classify_task(text)
        history_tasks = [c["task"] for c in self._context]

        # Adjust model weights using vector memory history
        try:
            records = vector_memory.query_vectors(
                filter={"type": "routing_decision", "emotion": emotion}, limit=10
            )
        except Exception:
            records = []

        mem_weights = dict(self._model_weights)
        for rec in records:
            m = rec.get("selected_model")
            if m in mem_weights:
                mem_weights[m] += 0.1

        emotion_model = self._model_from_emotion(emotion)
        mem_weights[emotion_model] = mem_weights.get(emotion_model, 1.0) + 0.2

        candidate = self._choose_model(
            task,
            weight,
            history_tasks,
            weights=mem_weights,
        )
        if mem_weights.get(candidate, 0.0) > mem_weights.get(emotion_model, 0.0):
            model = candidate
        else:
            model = emotion_model

        start = perf_counter()
        result: Dict[str, Any] = {
            "plane": plane,
            "archetype": archetype,
            "weight": weight,
            "model": model,
        }
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
            os.environ["CROWN_TTS_BACKEND"] = opts.get("tts_backend", "gtts")
            result.update(
                {
                    "tts_backend": opts.get("tts_backend"),
                    "avatar_style": opts.get("avatar_style"),
                    "aura_amount": opts.get("aura_amount"),
                }
            )
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

        if music_modality:
            hex_input = text.encode("utf-8").hex()
            phrases, wave = qnl_engine.hex_to_song(hex_input, duration_per_byte=0.05)
            wav_path = Path(tempfile.gettempdir()) / f"qnl_{abs(hash(hex_input))}.wav"
            sf.write(wav_path, wave, 44100)
            result["music_path"] = str(wav_path)
            result["qnl_phrases"] = phrases

        # Update lightweight context memory
        if self._embedder is not None:
            emb = np.asarray(self._embedder.encode([text]))[0]
        else:
            emb = np.array([len(text)], dtype=float)
        self._context.append({"text": text, "task": task, "embedding": emb})

        elapsed = perf_counter() - start
        if text_modality and "text" in result:
            self._benchmark(model, text, result["text"], elapsed)

        self._interaction_count += 1
        log_interaction(text, {"intents": intents or []}, result, "ok")

        if self._interaction_count % 20 == 0:
            entries = load_interactions()
            update_insights(entries)
            suggestions = learning_mutator.propose_mutations(load_insights())
            for s in suggestions:
                print(s)

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
                log_interaction(
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
                isinstance(res, dict)
                and res.get("status") in {"unhandled", "todo"}
            )
            training_guide.log_result(intent, success, qnl_data.get("tone"), res)
        emotion = qnl_data.get("tone", "neutral")
        self._update_mood(emotion)
        dominant = max(self.mood_state, key=self.mood_state.get)
        emotional_state.set_last_emotion(dominant)
        emotional_state.set_resonance_level(self.mood_state[dominant])

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

        symbols = self._invocation_engine._extract_symbols(text)
        tasks = ritual_action_sequence(symbols, dominant)
        for res in self._invocation_engine.invoke(f"{symbols} [{dominant}]", self):
            if isinstance(res, list):
                tasks.extend(res)
        for act in tasks:
            symbolic_parser.parse_intent({"text": act, "tone": dominant})

        emotion_data = {
            "emotion": dominant,
            "archetype": emotion_analysis.emotion_to_archetype(dominant),
            "weight": emotion_analysis.emotion_weight(dominant),
        }
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
            if "Extended" in meaning:
                steps = self._invocation_engine.invoke_ritual("silence_introspection")
                log_ritual_result("silence_introspection", steps)
        except Exception:
            pass

        return result


def schedule_action(func: Callable[[], Any], delay: float) -> threading.Timer:
    """Execute ``func`` after ``delay`` seconds using a timer."""
    timer = threading.Timer(delay, func)
    timer.start()
    return timer


__all__ = ["MoGEOrchestrator", "schedule_action"]
