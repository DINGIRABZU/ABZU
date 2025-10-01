"""Runtime helpers for Stage automation scripts."""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import json
import logging
import os
import shutil
import sys
import types
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, MutableMapping

if __name__ == "_stage_runtime":
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(Path(__file__).resolve().parent)]
        sys.modules["scripts"] = package
    sys.modules.setdefault("scripts._stage_runtime", sys.modules[__name__])

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
_FORCE_SANDBOX_ENV = bool(os.getenv("ABZU_FORCE_STAGE_SANDBOX"))
_force_sandbox_runtime = _FORCE_SANDBOX_ENV
_AUDIO_STACK_MISSING = any(shutil.which(binary) is None for binary in ("ffmpeg", "sox"))
_FORCED_MODULES = {
    "crown_decider",
    "crown_prompt_orchestrator",
    "emotional_state",
    "neoapsu_crown",
    "neoapsu_identity",
    "neoapsu_memory",
    "servant_model_manager",
    "state_transition_engine",
    "INANNA_AI.glm_integration",
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


def _neoabzu_candidate_dirs(root: Path) -> list[Path]:
    """Return directories that may contain Neo‑ABZU extension artifacts."""

    candidates: list[Path] = []
    override = os.getenv("NEOABZU_MEMORY_LIB_DIR")
    if override:
        candidates.append(Path(override))
    release_root = root / "target" / "release"
    candidates.append(release_root)
    candidates.append(release_root / "deps")
    neo_root = root / "NEOABZU"
    candidates.append(neo_root / "target" / "release")
    candidates.append(neo_root / "target" / "release" / "deps")
    candidates.append(neo_root / "memory" / "target" / "release")
    candidates.append(neo_root / "memory" / "target" / "release" / "deps")
    candidates.append(neo_root / "core" / "target" / "release")
    candidates.append(neo_root / "core" / "target" / "release" / "deps")
    seen: set[Path] = set()
    ordered: list[Path] = []
    for candidate in candidates:
        if candidate.exists():
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                ordered.append(resolved)
    return ordered


def _locate_extension(name: str, root: Path) -> Path | None:
    """Find the compiled extension ``name`` under ``root``."""

    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    prefixes = ("", "lib")
    for directory in _neoabzu_candidate_dirs(root):
        for prefix in prefixes:
            for suffix in suffixes:
                candidate = directory / f"{prefix}{name}{suffix}"
                if candidate.exists() and candidate.is_file():
                    return candidate
        for suffix in suffixes:
            for prefix in prefixes:
                for candidate in sorted(directory.glob(f"{prefix}{name}*{suffix}")):
                    if candidate.is_file():
                        return candidate
    return None


def _load_native_module(name: str, path: Path) -> types.ModuleType:
    """Load a compiled extension module from ``path``."""

    loader = importlib.machinery.ExtensionFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise ImportError(f"Unable to create module spec for {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    sys.modules[name] = module
    return module


def _ensure_native_module(name: str, root: Path) -> bool:
    """Attempt to load the native implementation for ``name`` if present."""

    module = sys.modules.get(name)
    if module is not None and not getattr(module, "__neoabzu_sandbox__", False):
        return True

    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError:
        module = None
    except ImportError:
        module = None
    if module is not None and not getattr(module, "__neoabzu_sandbox__", False):
        return True

    artifact = _locate_extension(name, root)
    if artifact is None:
        return False

    try:
        module = _load_native_module(name, artifact)
    except Exception as exc:  # pragma: no cover - loader failures vary
        warnings.warn(
            (
                "environment-limited: failed to load neoabzu_memory from "
                f"{artifact}: {exc}"
            ),
            EnvironmentLimitedWarning,
            stacklevel=3,
        )
        return False

    _APPLIED_OVERRIDES.pop(name, None)
    return True


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
        "neoabzu_memory",
        _make_neoabzu_memory_stub,
        "neoabzu_memory: optional bundle shim activated",
    )
    register(
        "neoapsu_memory",
        _make_neoapsu_memory_stub,
        "neoapsu_memory: sandbox contract suite shim activated",
    )
    register(
        "neoapsu_crown",
        _make_neoapsu_crown_stub,
        "neoapsu_crown: sandbox contract suite shim activated",
    )
    register(
        "neoapsu_identity",
        _make_neoapsu_identity_stub,
        "neoapsu_identity: sandbox contract suite shim activated",
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
    register(
        "prometheus_fastapi_instrumentator",
        _make_prometheus_instrumentator_stub,
        "prometheus instrumentation disabled in sandbox",
    )
    register(
        "INANNA_AI.glm_integration",
        _make_glm_integration_stub,
        "glm_integration: remote health check bypassed",
    )

    _DEFAULT_OVERRIDES_REGISTERED = True


def _should_force_override(name: str) -> bool:
    """Return ``True`` when ``name`` should always use the sandbox stub."""

    if name in _FORCED_MODULES:
        return _force_sandbox_runtime or _AUDIO_STACK_MISSING
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
        try:
            spec = importlib.util.find_spec(name)
        except ValueError:  # pragma: no cover - malformed module spec
            spec = None
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


def _emit_sandbox_log(
    message: str,
    logger: logging.Logger | Callable[[str], None] | None,
) -> None:
    """Emit ``message`` using ``logger`` or stdout as a fallback."""

    if logger is None:
        print(message)
        return
    if isinstance(logger, logging.Logger):
        logger.info(message)
        return
    try:
        logger(message)
    except Exception:  # pragma: no cover - defensive logging fallback
        logging.getLogger(__name__).info(message)


def _publish_environment_metadata() -> None:
    """Expose applied overrides via the environment for subprocesses."""

    if not _APPLIED_OVERRIDES:
        os.environ.pop("ABZU_SANDBOX_OVERRIDES", None)
        return
    os.environ["ABZU_SANDBOX_OVERRIDES"] = json.dumps(get_sandbox_overrides())


def bootstrap(
    optional_modules: Iterable[str] | None = None,
    *,
    sandbox: bool | None = None,
    log_summary: bool = False,
    summary_logger: logging.Logger | Callable[[str], None] | None = None,
) -> Path:
    """Prepare the Stage runtime and return the repository root."""

    _register_default_overrides()

    global _force_sandbox_runtime
    original_force = _force_sandbox_runtime
    if sandbox is not None:
        _force_sandbox_runtime = sandbox

    try:
        root = _detect_repo_root()
        _ensure_path(root)

        for module_name in (
            "neoabzu_memory",
            "neoabzu_core",
            "neoapsu_memory",
            "neoapsu_crown",
            "neoapsu_identity",
        ):
            if _ensure_native_module(module_name, root):
                continue

        for candidate in _neoabzu_candidate_dirs(root):
            if candidate.exists():
                _ensure_path(candidate)

        src_dir = root / "src"
        if src_dir.exists():
            _ensure_path(src_dir)

        _prepare_overrides()

        requested_modules = tuple(optional_modules or ())
        for name in requested_modules:
            if name in _SANDBOX_OVERRIDES:
                if not _ensure_native_module(name, root):
                    _maybe_stub(name, force=True)
                continue
            try:
                importlib.import_module(name)
            except Exception:  # pragma: no cover - import errors vary per sandbox
                warnings.warn(
                    f"environment-limited: optional module '{name}' unavailable",
                    EnvironmentLimitedWarning,
                    stacklevel=3,
                )

        _publish_environment_metadata()

        overrides = get_sandbox_overrides()
        should_log = log_summary or (sandbox and overrides)
        if should_log or (log_summary and not overrides):
            message = format_sandbox_summary("stage runtime sandbox")
            _emit_sandbox_log(message, summary_logger)

        return root
    finally:
        _force_sandbox_runtime = original_force


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


def _make_neoabzu_memory_stub() -> types.ModuleType:
    module = types.ModuleType("neoabzu_memory")

    try:  # pragma: no cover - heavy optional import varies per sandbox
        from memory.optional import neoabzu_bundle as _fallback_bundle
    except Exception:
        warnings.warn(
            (
                "environment-limited: neoabzu optional bundle unavailable; "
                "using minimal sandbox MemoryBundle"
            ),
            EnvironmentLimitedWarning,
            stacklevel=3,
        )

        class MemoryBundle:  # type: ignore[override]
            """Emergency fallback when both the Rust and Python bundles fail."""

            fallback_reason = "neoabzu_memory_unavailable"
            bundle_source = "scripts._stage_runtime.neoabzu_stub"
            bundle_mode = "stubbed"
            runtime_stubbed = True

            def __init__(self, *args, **kwargs) -> None:  # pragma: no cover
                self.args = args
                self.kwargs = kwargs
                self.stubbed = True
                self.bundle_source = getattr(
                    self, "bundle_source", MemoryBundle.bundle_source
                )
                self.bundle_mode = getattr(
                    self, "bundle_mode", MemoryBundle.bundle_mode
                )
                self.fallback_reason = getattr(
                    self, "fallback_reason", MemoryBundle.fallback_reason
                )

            def initialize(self) -> dict[str, object]:
                return {
                    "statuses": {},
                    "diagnostics": {},
                    "stubbed": True,
                    "fallback_reason": self.fallback_reason,
                    "bundle_source": self.bundle_source,
                    "bundle_mode": self.bundle_mode,
                }

            def query(self, _text: str) -> dict[str, object]:
                return {"stubbed": True, "failed_layers": []}

        module.MemoryBundle = MemoryBundle
    else:

        class MemoryBundle(_fallback_bundle.MemoryBundle):  # type: ignore[misc]
            """Stage sandbox shim delegating to the Python fallback bundle."""

            runtime_stubbed = True

            def __init__(
                self,
                *args,
                import_error: BaseException | None = None,
                **kwargs,
            ) -> None:
                if import_error is None:
                    import_error = ModuleNotFoundError(
                        "neoabzu_memory extension not installed (sandbox shim)"
                    )
                super().__init__(import_error=import_error)  # type: ignore[arg-type]
                self.stubbed = True
                self.bundle_source = getattr(
                    self, "bundle_source", "memory.optional.neoabzu_bundle"
                )
                self.bundle_mode = getattr(self, "bundle_mode", "stubbed")
                self.fallback_reason = getattr(
                    self, "fallback_reason", "neoabzu_memory_unavailable"
                )

        MemoryBundle.__module__ = module.__name__
        module.MemoryBundle = MemoryBundle

    module.__neoabzu_sandbox__ = True
    module.__sandbox_runtime__ = "scripts._stage_runtime"
    module.__all__ = ["MemoryBundle"]
    return module


def _make_neoapsu_contract_stub(name: str, suite: str) -> types.ModuleType:
    """Create a sandbox contract stub for Neo‑APSU verification modules."""

    module = types.ModuleType(name)

    def run_contract_suite(**kwargs: object) -> dict[str, object]:  # pragma: no cover
        fixtures: dict[str, object] = {}
        if kwargs:
            fixtures = {
                key: value for key, value in kwargs.items() if value is not None
            }
        tests = [
            {
                "id": f"{name}-import",
                "name": "import",
                "status": "skipped",
                "reason": "native bindings unavailable in sandbox",
            },
            {
                "id": f"{name}-fixtures",
                "name": "fixtures",
                "status": "skipped",
                "reason": "contract suite stub executed",
            },
        ]
        return {
            "suite": suite,
            "status": "stubbed",
            "sandbox": True,
            "tests": tests,
            "notes": [
                "sandbox stub executed in place of native Neo-APSU bindings",
            ],
            "fixtures": fixtures,
        }

    module.run_contract_suite = run_contract_suite  # type: ignore[attr-defined]
    module.SUITE_NAME = suite  # type: ignore[attr-defined]
    module.__neoapsu_sandbox__ = True
    module.__neoabzu_sandbox__ = True
    module.__sandbox_runtime__ = "scripts._stage_runtime"
    module.__all__ = ["run_contract_suite", "SUITE_NAME"]
    return module


def _make_neoapsu_memory_stub() -> types.ModuleType:
    return _make_neoapsu_contract_stub("neoapsu_memory", "Neo-APSU Memory")


def _make_neoapsu_crown_stub() -> types.ModuleType:
    return _make_neoapsu_contract_stub("neoapsu_crown", "Neo-APSU Crown")


def _make_neoapsu_identity_stub() -> types.ModuleType:
    return _make_neoapsu_contract_stub("neoapsu_identity", "Neo-APSU Identity")


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

    import asyncio as _asyncio
    import hashlib
    import inspect as _inspect

    registry: dict[str, Callable[[str], object]] = {}

    def register_model(name: str, handler: Callable[[str], object]) -> None:
        registry[name] = handler

    def unregister_model(name: str) -> None:
        registry.pop(name, None)

    def reload_model(name: str, handler: Callable[[str], object]) -> None:
        registry[name] = handler

    def register_subprocess_model(name: str, command: list[str]) -> None:
        """Register a deterministic sandbox subprocess stub."""

        def _handler(prompt: str) -> str:
            digest = hashlib.sha256(" ".join(command + [prompt]).encode("utf-8"))
            return f"{name}:{digest.hexdigest()[:12]}"

        registry[name] = _handler

    def list_models() -> list[str]:
        return sorted(registry)

    def has_model(name: str) -> bool:
        return name in registry

    async def invoke(name: str, prompt: str) -> str:
        handler = registry.get(name)
        if handler is None:
            raise KeyError(name)
        result = handler(prompt)
        if _inspect.isawaitable(result):
            result = await result  # pragma: no cover - async handler path
        return str(result)

    def invoke_sync(name: str, prompt: str) -> str:
        handler = registry.get(name)
        if handler is None:
            raise KeyError(name)
        result = handler(prompt)
        if _inspect.isawaitable(result):
            loop = _asyncio.new_event_loop()
            try:
                return str(loop.run_until_complete(result))
            finally:
                loop.close()
        return str(result)

    def _sandbox_digest(prefix: str, prompt: str) -> str:
        digest = hashlib.sha256(f"{prefix}:{prompt}".encode("utf-8"))
        return f"{prefix}:{digest.hexdigest()[:12]}"

    def register_kimi_k2() -> None:
        def _kimi_stub(prompt: str) -> str:
            return _sandbox_digest("kimi_k2", prompt)

        register_model("kimi_k2", _kimi_stub)

    def register_opencode() -> None:
        def _opencode_stub(prompt: str) -> str:
            return _sandbox_digest("opencode", prompt)

        register_model("opencode", _opencode_stub)

    def pulse_metrics(name: str) -> dict[str, float]:
        return {"avg_latency": 0.0, "failure_rate": 0.0}

    module.register_model = register_model
    module.unregister_model = unregister_model
    module.reload_model = reload_model
    module.register_subprocess_model = register_subprocess_model
    module.list_models = list_models
    module.has_model = has_model
    module.invoke = invoke
    module.invoke_sync = invoke_sync
    module.register_kimi_k2 = register_kimi_k2
    module.register_opencode = register_opencode
    module.pulse_metrics = pulse_metrics
    module.__all__ = [
        "register_model",
        "unregister_model",
        "reload_model",
        "register_subprocess_model",
        "list_models",
        "has_model",
        "invoke",
        "invoke_sync",
        "register_kimi_k2",
        "register_opencode",
        "pulse_metrics",
    ]
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


def _make_prometheus_instrumentator_stub() -> types.ModuleType:
    module = types.ModuleType("prometheus_fastapi_instrumentator")

    class Instrumentator:  # pragma: no cover - simple sandbox stub
        def instrument(self, app=None):  # type: ignore[override]
            return self

        def expose(self, app=None, **kwargs):  # type: ignore[override]
            return self

    module.Instrumentator = Instrumentator
    module.__all__ = ["Instrumentator"]
    return module


def _make_crown_orchestrator_stub() -> types.ModuleType:
    module = types.ModuleType("crown_prompt_orchestrator")

    from datetime import datetime
    import hashlib

    state_mod = sys.modules.get("state_transition_engine")
    if state_mod is None:
        _apply_override(
            "state_transition_engine",
            force=_should_force_override("state_transition_engine"),
        )
        state_mod = sys.modules.get("state_transition_engine")
    if state_mod is None:  # pragma: no cover - defensive guard
        raise RuntimeError("state_transition_engine sandbox stub unavailable")
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


def _make_glm_integration_stub() -> types.ModuleType:
    module = types.ModuleType("INANNA_AI.glm_integration")

    DEFAULT_ENDPOINT = "sandbox://glm"
    SAFE_ERROR_MESSAGE = "GLM unavailable (sandbox stub)"

    class GLMIntegration:
        """Deterministic stand-in for the networked GLM integration."""

        def __init__(
            self,
            endpoint: str | None = None,
            api_key: str | None = None,
            temperature: float = 0.8,
        ) -> None:
            self.endpoint = endpoint or DEFAULT_ENDPOINT
            self.api_key = api_key
            self.temperature = temperature
            self._history: list[tuple[str, str | None]] = []

        @property
        def headers(self) -> dict[str, str] | None:
            if self.api_key:
                return {"Authorization": f"Bearer {self.api_key}"}
            return None

        def health_check(self) -> None:
            """Pretend the remote health check succeeded."""

        def _summarize(self, prompt: str) -> str:
            preview = " ".join(prompt.strip().split())
            if not preview:
                preview = "<empty prompt>"
            return preview[:120]

        def complete(self, prompt: str, *, quantum_context: str | None = None) -> str:
            self._history.append((prompt, quantum_context))
            summary = self._summarize(prompt)
            ctx = f" ctx={quantum_context}" if quantum_context else ""
            return f"[sandbox-glm]{ctx} {summary}"

        async def complete_async(
            self, prompt: str, *, quantum_context: str | None = None
        ) -> str:
            return self.complete(prompt, quantum_context=quantum_context)

    module.GLMIntegration = GLMIntegration
    module.DEFAULT_ENDPOINT = DEFAULT_ENDPOINT
    module.SAFE_ERROR_MESSAGE = SAFE_ERROR_MESSAGE
    module.__all__ = ["GLMIntegration", "DEFAULT_ENDPOINT", "SAFE_ERROR_MESSAGE"]
    return module
