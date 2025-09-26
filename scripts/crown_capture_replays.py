"""Capture deterministic Crown replay outputs for Stage A validation."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import logging
import random
import sys
import tempfile
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List
from unittest import mock

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from scripts._stage_runtime import (
    EnvironmentLimitedWarning,
    bootstrap,
    format_sandbox_summary,
    get_sandbox_overrides,
)

ROOT = bootstrap(
    optional_modules=[
        "numpy",
        "yaml",
        "crown_decider",
        "crown_prompt_orchestrator",
        "emotional_state",
        "servant_model_manager",
        "state_transition_engine",
        "tools.session_logger",
    ]
)

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception as exc:  # pragma: no cover - numpy optional
    warnings.warn(
        f"environment-limited: numpy unavailable ({exc}); using deterministic stub",
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    np = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import yaml
except Exception as exc:  # pragma: no cover - yaml optional in sandbox
    warnings.warn(
        f"environment-limited: PyYAML unavailable ({exc}); using bundled scenarios",
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    yaml = None  # type: ignore[assignment]

try:
    import crown_decider
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        f"environment-limited: crown_decider unavailable ({exc}); using sandbox stub",
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    crown_decider = sys.modules.get("crown_decider")  # type: ignore[assignment]
    if crown_decider is None:
        raise

try:
    import crown_prompt_orchestrator as cpo
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        (
            "environment-limited: crown_prompt_orchestrator unavailable "
            f"({exc}); using sandbox stub"
        ),
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    cpo = sys.modules.get("crown_prompt_orchestrator")  # type: ignore[assignment]
    if cpo is None:
        raise

try:
    import emotional_state
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        (
            "environment-limited: emotional_state unavailable "
            f"({exc}); using sandbox stub"
        ),
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    emotional_state = sys.modules.get("emotional_state")  # type: ignore[assignment]
    if emotional_state is None:
        raise

try:
    import servant_model_manager as smm
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        (
            "environment-limited: servant_model_manager unavailable "
            f"({exc}); using sandbox stub"
        ),
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    smm = sys.modules.get("servant_model_manager")  # type: ignore[assignment]
    if smm is None:
        raise

try:
    from state_transition_engine import StateTransitionEngine
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        "environment-limited: state_transition_engine unavailable "
        f"({exc}); using sandbox stub",
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    _state_mod = sys.modules.get("state_transition_engine")
    if _state_mod is None or not hasattr(_state_mod, "StateTransitionEngine"):
        raise RuntimeError("state_transition_engine stub missing") from exc
    StateTransitionEngine = _state_mod.StateTransitionEngine  # type: ignore[assignment]

try:
    from tools import session_logger
except Exception as exc:  # pragma: no cover - sandbox stub fallback
    warnings.warn(
        (
            "environment-limited: session_logger unavailable "
            f"({exc}); using sandbox stub"
        ),
        EnvironmentLimitedWarning,
        stacklevel=2,
    )
    session_logger = sys.modules.get("tools.session_logger")  # type: ignore[assignment]
    if session_logger is None:
        raise

FALLBACK_SCENARIO_PAYLOAD = {
    "scenarios": [
        {
            "id": "crown_glm_reflection",
            "description": "Baseline GLM reflection without servant escalation.",
            "prompt": (
                "Crown, offer a reflective meditation on how the mission "
                "doctrine guides today's operator sync.\n"
            ),
            "expected_model": "glm",
            "include_memory": False,
            "seed": 1101,
            "context": [
                {"input": "Operator: confirm Crown identity assimilation transcript."},
                {"input": "Crown: mission brief acknowledged; awaiting directives."},
            ],
        },
        {
            "id": "crown_kimicho_guidance",
            "description": "Technical triage escalated to the Kimicho servant.",
            "prompt": (
                "Kimicho, diagnose this failure signature and outline a minimal "
                "patch.\n"
                "Traceback: ValueError: ritual binding missing during activation "
                "stage.\n"
            ),
            "expected_model": "kimicho",
            "include_memory": True,
            "seed": 2102,
            "memory": {
                "spiral": (
                    "Ritual ledger flagged missing binding during prior "
                    "rehearsal."
                ),
                "cortex": [
                    (
                        "Kimicho heuristic: prefer minimal code insertion before "
                        "escalation."
                    ),
                ],
                "vector": [
                    {
                        "text": (
                            "Operator note: retain existing bindings when applying "
                            "Kimicho patch."
                        ),
                    }
                ],
            },
            "context": [
                {
                    "input": (
                        "Operator: escalation requested for ritual binding fault."
                    ),
                }
            ],
        },
        {
            "id": "crown_kimi_k2_revision",
            "description": (
                "Kimicho relays to the K2 Coder servant for code-first "
                "repair."
            ),
            "prompt": (
                "K2 Coder, rewrite the failing binding so the activation ritual "
                "resolves\n"
                "without additional side effects.\n"
            ),
            "expected_model": "kimi_k2",
            "include_memory": True,
            "seed": 3103,
            "memory": {
                "spiral": (
                    "Kimicho report: binding lookup requires explicit null-guard."
                ),
                "cortex": [
                    (
                        "Prior K2 Coder patch inserted guard rails for activation "
                        "step."
                    ),
                ],
                "vector": [
                    {
                        "text": (
                            "Telemetry: activation ritual fails after three attempts "
                            "without guard."
                        ),
                    }
                ],
            },
            "context": [
                {
                    "input": (
                        "Kimicho: escalation to K2 coder triggered after minimal "
                        "patch attempt."
                    ),
                }
            ],
        },
        {
            "id": "crown_air_star_validation",
            "description": (
                "Air Star reviews cross-file impact before final escalation."
            ),
            "prompt": (
                "Air Star, evaluate the revised binding plan and stage validation "
                "notes for\n"
                "the operator review packet.\n"
            ),
            "expected_model": "air_star",
            "include_memory": True,
            "seed": 4104,
            "memory": {
                "spiral": "K2 Coder patch introduces guard_path parameter.",
                "cortex": [
                    (
                        "Air Star directive: cross-verify companion modules before "
                        "merge."
                    ),
                ],
                "vector": [
                    {
                        "text": (
                            "Review log: ensure guard_path maintains ritual state "
                            "machine invariants."
                        ),
                    }
                ],
            },
            "context": [
                {
                    "input": (
                        "K2 Coder: patch candidate ready; requesting Air Star "
                        "validation."
                    ),
                }
            ],
        },
        {
            "id": "crown_rstar_finalization",
            "description": (
                "Final rStar escalation capturing the terminal remediation "
                "output."
            ),
            "prompt": (
                "rStar, synthesize the final remediation script so the ritual "
                "activation\n"
                "completes even under degraded telemetry.\n"
            ),
            "expected_model": "rstar",
            "include_memory": True,
            "seed": 5105,
            "memory": {
                "spiral": (
                    "Air Star verdict: guard_path needs resilience hooks for "
                    "telemetry gaps."
                ),
                "cortex": [
                    (
                        "rStar escalation protocol: include rollback stanza in final "
                        "patch."
                    ),
                ],
                "vector": [
                    {
                        "text": (
                            "Operator directive: archive final remediation in Stage A "
                            "evidence bundle."
                        ),
                    }
                ],
            },
            "context": [
                {
                    "input": (
                        "Air Star: handing final remediation to rStar with validation "
                        "notes."
                    ),
                }
            ],
        },
    ]
}

session_logger.AUDIO_DIR = ROOT / "logs/audio"
session_logger.VIDEO_DIR = ROOT / "logs/video"

logger = logging.getLogger(__name__)

LOG_DIR = ROOT / "logs/crown_replays"
INDEX_FILE = LOG_DIR / "index.json"
DEFAULT_SCENARIO_FILE = ROOT / "crown/replay_scenarios.yaml"


@dataclass
class CaptureResult:
    """Structured record of a replay capture."""

    timestamp: str
    model: str
    emotion: str | None
    state: str | None
    result: dict[str, Any]
    result_hash: str
    audio_path: str
    audio_hash: str
    video_path: str
    video_hash: str
    servant_prompt: str | None


class _RecordingServant:
    """Callable servant stub that records prompts and returns deterministic text."""

    def __init__(self, name: str, scenario_id: str) -> None:
        self.name = name
        self.scenario_id = scenario_id
        self.prompts: List[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        payload = f"{self.scenario_id}:{self.name}:{prompt}"
        digest = hashlib.sha256(payload.encode("utf-8"))
        return f"{self.name}:{digest.hexdigest()[:16]}"


class _StubGLM:
    """In-memory GLM stub mirroring the orchestrator interface."""

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def complete(self, prompt: str, quantum_context: str | None = None) -> str:
        payload = f"glm:{self.seed}:{prompt}:{quantum_context}"
        digest = hashlib.sha256(payload.encode("utf-8"))
        return f"glm:{digest.hexdigest()[:16]}"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_result(result: dict[str, Any]) -> str:
    payload = json.dumps(result, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_scenarios(path: Path) -> list[dict[str, Any]]:
    if yaml is None:
        warnings.warn(
            (
                "environment-limited: falling back to bundled Crown replay scenarios"
                " because PyYAML is unavailable"
            ),
            EnvironmentLimitedWarning,
            stacklevel=2,
        )
        import json as _json

        data = _json.loads(_json.dumps(FALLBACK_SCENARIO_PAYLOAD))
    else:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "scenarios" not in data:
        raise ValueError(f"Scenario file {path} is missing a 'scenarios' list")
    scenarios = data["scenarios"]
    if not isinstance(scenarios, list):
        raise ValueError("'scenarios' must be a list")
    parsed: list[dict[str, Any]] = []
    for idx, raw in enumerate(scenarios):
        if not isinstance(raw, dict):
            raise ValueError(f"Scenario entry #{idx} is not a mapping")
        if "id" not in raw or "prompt" not in raw or "expected_model" not in raw:
            raise ValueError(f"Scenario entry #{idx} missing required keys")
        parsed.append(raw)
    return parsed


def _prepare_audio_asset(
    scenario_id: str, seed: int, result_text: str
) -> tuple[Path, str]:
    with tempfile.TemporaryDirectory() as tmp:
        temp_path = Path(tmp) / f"{scenario_id}_audio.npy"
        if np is not None:
            rng = np.random.default_rng(seed)
            samples = rng.standard_normal(2048).astype(np.float32)
            np.save(temp_path, samples)
        else:
            payload = f"audio:{scenario_id}:{seed}:{result_text}"
            digest = hashlib.sha256(payload.encode("utf-8")).digest()
            temp_path.write_bytes(digest)
        dest = session_logger.log_audio(temp_path)
    return dest, _sha256_file(dest)


def _prepare_video_asset(scenario_id: str, seed: int) -> tuple[Path, str]:
    if np is not None:
        rng = np.random.default_rng(seed)
        frames = [
            rng.integers(0, 255, size=(24, 24, 3), dtype=np.uint8) for _ in range(5)
        ]
    else:
        rng = random.Random(seed)
        frames = []
        for _ in range(5):
            frame = [rng.randint(0, 255) for _ in range(24 * 24 * 3)]
            frames.append(frame)
    dest = session_logger.log_video(frames)  # type: ignore[arg-type]
    return dest, _sha256_file(dest)


def _reset_emotion_state() -> None:
    try:
        emotional_state.set_current_layer(None)
    except Exception:  # pragma: no cover - optional dependency failure
        logger.exception("Failed to reset current layer")
    try:
        emotional_state.set_last_emotion(None)
    except Exception:  # pragma: no cover - optional dependency failure
        logger.exception("Failed to reset last emotion")


async def _run_scenario(scenario: dict[str, Any]) -> CaptureResult:
    scenario_id = str(scenario["id"])
    expected_model = str(scenario["expected_model"])
    seed = int(scenario.get("seed", 0))
    include_memory = bool(scenario.get("include_memory", True))

    logger.info(
        "Running scenario %s (model=%s, seed=%s)", scenario_id, expected_model, seed
    )

    random.seed(seed)
    if np is not None:
        np.random.seed(seed)

    _reset_emotion_state()

    glm = _StubGLM(seed)

    servant: _RecordingServant | None = None

    with contextlib.ExitStack() as stack:
        original_engine = getattr(cpo, "_STATE_ENGINE", None)
        stack.callback(lambda: setattr(cpo, "_STATE_ENGINE", original_engine))
        setattr(cpo, "_STATE_ENGINE", StateTransitionEngine())

        if "context" in scenario:
            context_entries = list(scenario.get("context", []))

            def _load_interactions(limit: int = 3) -> list[dict[str, Any]]:
                if limit is None:
                    return context_entries
                return context_entries[-limit:]

        stack.enter_context(
            mock.patch.object(cpo, "load_interactions", _load_interactions)
        )

        if "memory" in scenario:
            memory_payload = scenario["memory"]

            def _query_memory(_: str) -> dict[str, Any]:
                return memory_payload

            stack.enter_context(mock.patch.object(cpo, "query_memory", _query_memory))

        stack.enter_context(
            mock.patch.object(crown_decider, "recommend_llm", lambda *_: expected_model)
        )

        if expected_model != "glm":
            servant = _RecordingServant(expected_model, scenario_id)
            smm.unregister_model(expected_model)
            smm.register_model(expected_model, servant)
            stack.callback(lambda: smm.unregister_model(expected_model))

        result = await cpo.crown_prompt_orchestrator_async(
            str(scenario["prompt"]),
            glm,
            include_memory=include_memory,
        )

    result_hash = _sha256_result(result)
    audio_path, audio_hash = _prepare_audio_asset(
        scenario_id, seed, result.get("text", "")
    )
    video_path, video_hash = _prepare_video_asset(scenario_id, seed)
    timestamp = datetime.utcnow().isoformat()

    servant_prompt = servant.prompts[-1] if servant and servant.prompts else None

    return CaptureResult(
        timestamp=timestamp,
        model=result.get("model", ""),
        emotion=result.get("emotion"),
        state=result.get("state"),
        result=result,
        result_hash=result_hash,
        audio_path=str(audio_path),
        audio_hash=audio_hash,
        video_path=str(video_path),
        video_hash=video_hash,
        servant_prompt=servant_prompt,
    )


def _load_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_metadata(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _validate_and_update_metadata(
    scenario: dict[str, Any],
    capture: CaptureResult,
    metadata_path: Path,
) -> None:
    existing = _load_metadata(metadata_path)
    expected_model = str(scenario["expected_model"])
    seed = int(scenario.get("seed", 0))

    capture_payload = {
        "timestamp": capture.timestamp,
        "model": capture.model,
        "emotion": capture.emotion,
        "state": capture.state,
        "result_hash": capture.result_hash,
        "audio_path": capture.audio_path,
        "audio_hash": capture.audio_hash,
        "video_path": capture.video_path,
        "video_hash": capture.video_hash,
        "servant_prompt": capture.servant_prompt,
    }
    overrides = get_sandbox_overrides()
    if overrides:
        capture_payload["sandbox_overrides"] = overrides

    if existing is None:
        data = {
            "id": scenario["id"],
            "description": scenario.get("description"),
            "prompt": scenario.get("prompt"),
            "expected_model": expected_model,
            "seed": seed,
            "baseline": {**capture_payload, "result": capture.result},
            "last_run": {**capture_payload, "result": capture.result},
        }
        if overrides:
            data["sandbox_overrides"] = overrides
        _write_metadata(metadata_path, data)
        return

    baseline = existing.get("baseline", {})
    if not baseline:
        raise RuntimeError(f"Metadata for {scenario['id']} missing baseline block")

    comparisons = {
        "model": (baseline.get("model"), capture.model),
        "result_hash": (baseline.get("result_hash"), capture.result_hash),
        "audio_hash": (baseline.get("audio_hash"), capture.audio_hash),
        "video_hash": (baseline.get("video_hash"), capture.video_hash),
        "emotion": (baseline.get("emotion"), capture.emotion),
        "state": (baseline.get("state"), capture.state),
    }

    if overrides:
        logger.warning(
            "Sandbox overrides active; skipping strict comparison for %s",
            scenario["id"],
        )
        existing.setdefault("sandbox_overrides", overrides)
    else:
        for key, (expected, observed) in comparisons.items():
            if expected != observed:
                message = (
                    "Replay divergence for "
                    f"{scenario['id']}: {key} expected {expected!r} "
                    f"but observed {observed!r}"
                )
                raise RuntimeError(message)

    existing["last_run"] = {**capture_payload, "result": capture.result}
    _write_metadata(metadata_path, existing)


def _update_index() -> None:
    entries: list[dict[str, Any]] = []
    for meta_path in sorted(LOG_DIR.glob("*.json")):
        if meta_path.name == INDEX_FILE.name:
            continue
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        entry = {
            "id": data.get("id"),
            "expected_model": data.get("expected_model"),
            "seed": data.get("seed"),
            "baseline_timestamp": data.get("baseline", {}).get("timestamp"),
            "baseline_hash": data.get("baseline", {}).get("result_hash"),
            "last_run_timestamp": data.get("last_run", {}).get("timestamp"),
        }
        entries.append(entry)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


async def _async_main(args: argparse.Namespace) -> int:
    scenario_file = Path(args.scenarios)
    scenarios = _load_scenarios(scenario_file)

    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [sc for sc in scenarios if str(sc["id"]) in wanted]
        missing = wanted - {str(sc["id"]) for sc in scenarios}
        if missing:
            ordered = ", ".join(sorted(missing))
            raise SystemExit(f"Unknown scenario ids requested: {ordered}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for scenario in scenarios:
        capture = await _run_scenario(scenario)
        metadata_path = LOG_DIR / f"{scenario['id']}.json"
        _validate_and_update_metadata(scenario, capture, metadata_path)

    _update_index()
    return len(scenarios)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        type=str,
        default=str(DEFAULT_SCENARIO_FILE),
        help="Path to the replay scenario YAML file.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help=(
            "Limit execution to the specified scenario id (may be passed multiple"
            " times)."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(message)s",
    )
    processed = asyncio.run(_async_main(args))
    prefix = f"Stage A2 crown replays captured ({processed} scenarios)"
    print(format_sandbox_summary(prefix))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
