"""Runtime helpers for Stage automation scripts."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import shutil
import sys
import types
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, MutableMapping

__all__ = [
    "EnvironmentLimitedWarning",
    "bootstrap",
    "get_sandbox_overrides",
    "format_sandbox_summary",
]


class EnvironmentLimitedWarning(UserWarning):
    """Warning emitted when optional modules are unavailable in the sandbox."""


@dataclass(frozen=True)
class _SandboxOverride:
    """Definition of a sandbox stub for a heavy dependency."""

    factory: Callable[[], types.ModuleType]
    note: str


_SANDBOX_OVERRIDES: MutableMapping[str, _SandboxOverride] = {}
_APPLIED_OVERRIDES: MutableMapping[str, str] = {}
_DEFAULT_OVERRIDES_REGISTERED = False
_FORCE_SANDBOX = bool(os.getenv("ABZU_FORCE_STAGE_SANDBOX"))
_AUDIO_STACK_MISSING = any(shutil.which(binary) is None for binary in ("ffmpeg", "sox"))
_FORCED_MODULES = {
    "crown_decider",
    "crown_prompt_orchestrator",
    "emotional_state",
    "servant_model_manager",
    "state_transition_engine",
}


def _detect_repo_root(start: Path | None = None) -> Path:
    """Heuristically locate the repository root from ``start``."""

    path = (start or Path(__file__)).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return path.parent


def _ensure_path(path: Path) -> None:
    """Insert ``path`` at the front of :data:`sys.path` if missing."""

    resolved = str(path)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def _register_default_overrides() -> None:
    """Populate :data:`_SANDBOX_OVERRIDES` with Stage A fallbacks."""

    global _DEFAULT_OVERRIDES_REGISTERED
    if _DEFAULT_OVERRIDES_REGISTERED:
        return

    def register(name: str, factory: Callable[[], types.ModuleType], note: str) -> None:
        _SANDBOX_OVERRIDES.setdefault(
            name,
            _SandboxOverride(factory=factory, note=note),
        )

    register(
        "env_validation",
        _make_env_validation_stub,
        "env_validation: required variable enforcement skipped",
    )
    register(
        "crown_decider",
        _make_crown_decider_stub,
        "crown_decider: recommendation heuristics simplified",
    )
    register(
        "crown_prompt_orchestrator",
        _make_crown_orchestrator_stub,
        "crown_prompt_orchestrator: async pipeline stubbed",
    )
    register(
        "emotional_state",
        _make_emotional_state_stub,
        "emotional_state: in-memory state used",
    )
    register(
        "servant_model_manager",
        _make_servant_model_manager_stub,
        "servant_model_manager: local registry only",
    )
    register(
        "state_transition_engine",
        _make_state_transition_engine_stub,
        "state_transition_engine: deterministic rotation",
    )
    register(
        "tools.session_logger",
        _make_session_logger_stub,
        "session_logger: binary dumps without ffmpeg",
    )

    _DEFAULT_OVERRIDES_REGISTERED = True


def _should_force_override(name: str) -> bool:
    """Return ``True`` when ``name`` should always use the sandbox stub."""

    if name in _FORCED_MODULES:
        return _FORCE_SANDBOX or _AUDIO_STACK_MISSING
    return False


def _apply_override(name: str, *, force: bool = False) -> bool:
    """Install ``name`` stub if available and record metadata."""

    if not force and name in sys.modules:
        return False
    override = _SANDBOX_OVERRIDES.get(name)
    if override is None:
        return False
    module = override.factory()
    sys.modules[name] = module
    _APPLIED_OVERRIDES[name] = override.note
    warnings.warn(
        f"environment-limited: activated sandbox stub for '{name}' ({override.note})",
        EnvironmentLimitedWarning,
        stacklevel=3,
    )
    _publish_environment_metadata()
    return True


def _maybe_stub(name: str, *, force: bool = False) -> None:
    """Attempt to import ``name`` and fallback to sandbox stub if it fails."""

    if force:
        _apply_override(name, force=True)
        return
    try:
        importlib.import_module(name)
    except Exception:  # pragma: no cover - import errors vary per sandbox
        _apply_override(name)


def _prepare_overrides() -> None:
    """Eagerly activate overrides for modules missing from the sandbox."""

    for name in list(_SANDBOX_OVERRIDES):
        if name in sys.modules and not _should_force_override(name):
            continue
        spec = importlib.util.find_spec(name)
        if spec is None or _should_force_override(name):
            _apply_override(name, force=_should_force_override(name))


def get_sandbox_overrides() -> dict[str, str]:
    """Return a mapping of sandboxed modules to their descriptive notes."""

    return dict(_APPLIED_OVERRIDES)


def format_sandbox_summary(prefix: str | None = None) -> str:
    """Return a human-readable summary of active sandbox overrides."""

    overrides = get_sandbox_overrides()
    if not overrides:
        return prefix or "sandbox clean: no overrides"
    details = ", ".join(f"{name} ({note})" for name, note in sorted(overrides.items()))
    message = f"sandbox overrides active: {details}"
    if prefix:
        return f"{prefix} [{message}]"
    return message


def _publish_environment_metadata() -> None:
    """Expose applied overrides via the environment for subprocesses."""

    if not _APPLIED_OVERRIDES:
        os.environ.pop("ABZU_SANDBOX_OVERRIDES", None)
        return
    os.environ["ABZU_SANDBOX_OVERRIDES"] = json.dumps(get_sandbox_overrides())


def bootstrap(optional_modules: Iterable[str] | None = None) -> Path:
    """Prepare the Stage runtime and return the repository root."""

    _register_default_overrides()

    root = _detect_repo_root()
    _ensure_path(root)

    src_dir = root / "src"
    if src_dir.exists():
        _ensure_path(src_dir)

    _prepare_overrides()

    for name in optional_modules or ():
        _maybe_stub(name, force=_should_force_override(name))

    _publish_environment_metadata()
    return root


def _make_env_validation_stub() -> types.ModuleType:
    module = types.ModuleType("env_validation")

    def _warn(message: str) -> None:
        warnings.warn(message, EnvironmentLimitedWarning, stacklevel=3)

    def check_required(vars: Iterable[str]) -> None:  # type: ignore[override]
        missing = [name for name in vars if not os.getenv(name)]
        if missing:
            joined = ", ".join(sorted(set(missing)))
            _warn(
                "environment-limited: skipping strict env var enforcement; "
                f"missing {joined}"
            )

    def check_optional_packages(packages: Iterable[str]) -> None:  # pragma: no cover
        for pkg in packages:
            try:
                importlib.import_module(pkg)
            except Exception:
                _warn(f"optional package '{pkg}' unavailable in sandbox")

    def check_required_binaries(binaries: Iterable[str]) -> None:  # pragma: no cover
        missing = [name for name in binaries if shutil.which(name) is None]
        if missing:
            joined = ", ".join(sorted(missing))
            _warn(
                "environment-limited: required binaries missing; "
                f"continuing without {joined}"
            )

    def check_audio_binaries(*, require: bool = True) -> bool:  # pragma: no cover
        binaries = ["ffmpeg", "sox"]
        missing = [name for name in binaries if shutil.which(name) is None]
        if missing and require:
            joined = ", ".join(sorted(missing))
            _warn(
                "environment-limited: audio binaries missing; "
                f"continuing without {joined}"
            )
        return not missing

    def check_rl_packages() -> None:  # pragma: no cover
        check_optional_packages(["gymnasium", "numpy", "stable_baselines3"])

    def parse_servant_models(
        env: str | None = None, *, require: bool = False
    ) -> dict[str, str]:  # pragma: no cover - simple passthrough
        return {}

    import shutil

    module.check_required = check_required
    module.check_optional_packages = check_optional_packages
    module.check_required_binaries = check_required_binaries
    module.check_audio_binaries = check_audio_binaries
    module.check_rl_packages = check_rl_packages
    module.parse_servant_models = parse_servant_models
    module.__all__ = [
        "check_required",
        "check_optional_packages",
        "check_required_binaries",
        "check_audio_binaries",
        "check_rl_packages",
        "parse_servant_models",
    ]
    return module


def _make_crown_decider_stub() -> types.ModuleType:
    module = types.ModuleType("crown_decider")

    _registry: dict[str, list[bool]] = {}

    def record_result(name: str, success: bool) -> None:
        outcomes = _registry.setdefault(name, [])
        outcomes.append(success)

    def recommend_llm(task_type: str, emotion: str) -> str:
        return "glm"

    def decide_expression_options(emotion: str) -> dict[str, object]:
        return {
            "tts_backend": "text",
            "avatar_style": "sandbox",
            "aura_amount": 0.0,
            "aura": {"mode": "none"},
            "soul_state": "sandbox",
        }

    module.record_result = record_result
    module.recommend_llm = recommend_llm
    module.decide_expression_options = decide_expression_options
    module.__all__ = [
        "record_result",
        "recommend_llm",
        "decide_expression_options",
    ]
    return module


def _make_state_transition_engine_stub() -> types.ModuleType:
    module = types.ModuleType("state_transition_engine")

    class StateTransitionEngine:
        STATES = ("dormant", "active", "ritual")

        def __init__(self) -> None:
            self._state_index = 0

        def update_state(self, event: str) -> str:
            self._state_index = (self._state_index + 1) % len(self.STATES)
            return self.STATES[self._state_index]

        def current_state(self) -> str:
            return self.STATES[self._state_index]

    module.StateTransitionEngine = StateTransitionEngine
    module.__all__ = ["StateTransitionEngine"]
    return module


def _make_emotional_state_stub() -> types.ModuleType:
    module = types.ModuleType("emotional_state")

    state: dict[str, object | None] = {
        "current_layer": None,
        "last_emotion": None,
        "soul_state": None,
    }

    def get_current_layer() -> str | None:
        return state["current_layer"]  # type: ignore[return-value]

    def set_current_layer(value: str | None) -> None:
        state["current_layer"] = value

    def get_last_emotion() -> str | None:
        return state["last_emotion"]  # type: ignore[return-value]

    def set_last_emotion(value: str | None) -> None:
        state["last_emotion"] = value

    def get_soul_state() -> str | None:
        return state["soul_state"]  # type: ignore[return-value]

    module.get_current_layer = get_current_layer
    module.set_current_layer = set_current_layer
    module.get_last_emotion = get_last_emotion
    module.set_last_emotion = set_last_emotion
    module.get_soul_state = get_soul_state
    module.__all__ = [
        "get_current_layer",
        "set_current_layer",
        "get_last_emotion",
        "set_last_emotion",
        "get_soul_state",
    ]
    return module


def _make_servant_model_manager_stub() -> types.ModuleType:
    module = types.ModuleType("servant_model_manager")

    registry: dict[str, Callable[[str], str | object]] = {}

    def register_model(name: str, handler: Callable[[str], object]) -> None:
        registry[name] = handler

    def unregister_model(name: str) -> None:
        registry.pop(name, None)

    def list_models() -> list[str]:
        return sorted(registry)

    module.register_model = register_model
    module.unregister_model = unregister_model
    module.list_models = list_models
    module.__all__ = ["register_model", "unregister_model", "list_models"]
    return module


def _make_session_logger_stub() -> types.ModuleType:
    module = types.ModuleType("tools.session_logger")

    from pathlib import Path as _Path
    import shutil as _shutil

    AUDIO_DIR = _Path("logs/audio")
    VIDEO_DIR = _Path("logs/video")

    def _timestamp() -> str:
        from datetime import datetime

        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def log_audio(path: str | _Path) -> _Path:
        src = _Path(path)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        dest = AUDIO_DIR / f"{_timestamp()}{src.suffix or '.bin'}"
        try:
            _shutil.copy2(src, dest)
        except Exception:  # pragma: no cover - best effort copy
            dest.write_bytes(src.read_bytes())
        return dest

    def log_video(frames) -> _Path:  # type: ignore[override]
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        dest = VIDEO_DIR / f"{_timestamp()}.json"
        try:
            import json as _json

            payload = [getattr(frame, "tolist", lambda: frame)() for frame in frames]
            dest.write_text(_json.dumps(payload), encoding="utf-8")
        except Exception:  # pragma: no cover - fallback to binary
            dest.write_bytes(b"sandbox-video")
        return dest

    module.AUDIO_DIR = AUDIO_DIR
    module.VIDEO_DIR = VIDEO_DIR
    module.log_audio = log_audio
    module.log_video = log_video
    module.__all__ = ["log_audio", "log_video", "AUDIO_DIR", "VIDEO_DIR"]
    return module


def _make_crown_orchestrator_stub() -> types.ModuleType:
    module = types.ModuleType("crown_prompt_orchestrator")

    from datetime import datetime
    import hashlib

    state_mod = sys.modules.get("state_transition_engine")
    if state_mod is None:
        _maybe_stub("state_transition_engine")
        state_mod = sys.modules.get("state_transition_engine")
    StateTransitionEngine = getattr(state_mod, "StateTransitionEngine")

    _STATE_ENGINE = StateTransitionEngine()

    async def crown_prompt_orchestrator_async(
        message: str,
        glm: object,
        *,
        include_memory: bool = True,
    ) -> dict[str, object]:
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
        state = _STATE_ENGINE.update_state(message)
        text = None
        if hasattr(glm, "complete"):
            try:
                text = glm.complete(message, quantum_context=None)
            except TypeError:
                text = glm.complete(message)
        if text is None:
            text = f"glm:{digest[:12]}"
        return {
            "model": "glm",
            "text": str(text),
            "emotion": "neutral",
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
            "sandbox": True,
            "digest": digest,
        }

    def load_interactions(limit: int = 3) -> list[dict[str, object]]:
        return []

    def query_memory(_: str) -> dict[str, object]:
        return {}

    module._STATE_ENGINE = _STATE_ENGINE
    module.crown_prompt_orchestrator_async = crown_prompt_orchestrator_async
    module.load_interactions = load_interactions
    module.query_memory = query_memory
    module.__all__ = [
        "crown_prompt_orchestrator_async",
        "load_interactions",
        "query_memory",
        "_STATE_ENGINE",
    ]
    return module
