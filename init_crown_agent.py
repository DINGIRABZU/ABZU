# Patent pending – see PATENTS.md
"""Initialize the crown agent and optional vector memory subsystem."""

from __future__ import annotations

__version__ = "0.1.0"

import logging
import os
from pathlib import Path

import yaml  # type: ignore[import-untyped]

import servant_model_manager as smm
from env_validation import parse_servant_models
from INANNA_AI import corpus_memory
from INANNA_AI.glm_integration import GLMIntegration

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]

try:  # pragma: no cover - enforce dependency
    import requests  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover - requests must be installed
    raise ImportError(
        "init_crown_agent requires the 'requests' package."
        " Install it via 'pip install requests'."
    ) from exc

try:  # pragma: no cover - optional dependency
    from prometheus_client import Gauge
except Exception:  # pragma: no cover - optional dependency
    Gauge = None  # type: ignore[assignment]

SERVANT_HEALTH_GAUGE = (
    Gauge("servant_health_status", "1=healthy,0=unhealthy", ["servant"])
    if Gauge is not None
    else None
)

vector_memory = _vector_memory  # Optional vector memory subsystem

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parent / "config" / "INANNA_CORE.yaml"


def _load_config() -> dict:
    """Return configuration merged with environment overrides."""
    cfg: dict = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    env_map = {
        "glm_api_url": "GLM_API_URL",
        "glm_api_key": "GLM_API_KEY",
        "model_path": "MODEL_PATH",
        "memory_dir": "MEMORY_DIR",
    }
    for key, env in env_map.items():
        val = os.getenv(env)
        if val:
            cfg[key] = val
            logger.info("%s loaded from env %s", key, env)

    servant = dict(cfg.get("servant_models", {}))
    for name, env in (
        ("deepseek", "DEEPSEEK_URL"),
        ("mistral", "MISTRAL_URL"),
        ("kimi_k2", "KIMI_K2_URL"),
    ):
        val = os.getenv(env)
        if val:
            if name in servant:
                logger.warning(
                    "Duplicate servant model name '%s' from %s; keeping existing",
                    name,
                    env,
                )
                continue
            servant[name] = val
            logger.info("servant %s url loaded from env %s", name, env)
    if servant:
        cfg["servant_models"] = servant

    return cfg


def _init_memory(cfg: dict) -> None:
    mem_dir = cfg.get("memory_dir")
    if mem_dir:
        mem_dir = Path(mem_dir)
        vec_path = mem_dir / "vector_memory"
        corpus_path = mem_dir / "chroma"
        vec_path.mkdir(parents=True, exist_ok=True)
        corpus_path.mkdir(parents=True, exist_ok=True)
        logger.info("memory directories created: %s, %s", vec_path, corpus_path)

        os.environ["VECTOR_DB_PATH"] = str(vec_path)
        logger.info("initializing vector memory at %s", vec_path)
        if vector_memory is not None:
            try:
                vector_memory._get_collection()
                logger.info("Vector memory loaded from %s", vec_path)
            except Exception as exc:  # pragma: no cover - optional deps
                logger.warning("Vector memory unavailable: %s", exc)
        else:  # pragma: no cover - optional dependency missing
            logger.warning("Vector memory module missing; related features disabled")

        corpus_memory.CHROMA_DIR = corpus_path
        logger.info("initializing corpus memory at %s", corpus_path)
        try:
            corpus_memory.create_collection(dir_path=corpus_memory.CHROMA_DIR)
            logger.info("Corpus memory loaded from %s", corpus_path)
        except Exception as exc:  # pragma: no cover - optional deps
            logger.warning("Corpus memory unavailable: %s", exc)


def _check_glm(integration: GLMIntegration) -> None:
    try:
        integration.health_check()
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("GLM health check failed: %s", exc)
        raise RuntimeError("GLM endpoint unavailable") from exc
    logger.info("GLM health check succeeded")


def _register_http_servant(name: str, url: str) -> None:
    def _invoke(prompt: str) -> str:
        try:
            resp = requests.post(url, json={"prompt": prompt}, timeout=10)
            resp.raise_for_status()
            try:
                return resp.json().get("text", "")
            except Exception:
                return resp.text
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Servant %s failed: %s", name, exc)
            return ""

    smm.register_model(name, _invoke)


def _init_servants(cfg: dict) -> None:
    servants = dict(cfg.get("servant_models") or {})
    kimi_url = servants.pop("kimi_k2", None) or os.getenv("KIMI_K2_URL")
    opencode_present = "opencode" in servants or os.getenv("OPENCODE_URL")
    opencode_url = servants.pop("opencode", None) or os.getenv("OPENCODE_URL")
    if kimi_url:
        os.environ.setdefault("KIMI_K2_URL", kimi_url)
        smm.register_kimi_k2()
    if opencode_present:
        if opencode_url:
            os.environ.setdefault("OPENCODE_URL", opencode_url)
        smm.register_opencode()
    for name, url in servants.items():
        _register_http_servant(name, url)


def _verify_servant_health(servants: dict) -> None:
    """Check that each servant model responds to a health request."""
    if not servants:
        return
    failed: list[str] = []
    for name, url in servants.items():
        health_url = url.rstrip("/") + "/health"
        healthy = False
        try:
            resp = requests.get(health_url, timeout=5)
            resp.raise_for_status()
            logger.info("Servant %s healthy at %s", name, health_url)
            healthy = True
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Servant %s health check failed: %s", name, exc)
            failed.append(name)
        if SERVANT_HEALTH_GAUGE is not None:
            SERVANT_HEALTH_GAUGE.labels(servant=name).set(1 if healthy else 0)
    if failed:
        raise SystemExit(f"Unavailable servant models: {', '.join(failed)}")


def initialize_crown() -> GLMIntegration:
    """Return a :class:`GLMIntegration` instance configured from YAML."""
    cfg = _load_config()
    servants = dict(cfg.get("servant_models") or {})
    env_servants = parse_servant_models(require=True)
    if env_servants:
        for name, url in env_servants.items():
            if name in servants:
                logger.warning(
                    "Duplicate servant model name '%s' in SERVANT_MODELS; "
                    "keeping existing",
                    name,
                )
                continue
            servants[name] = url
        cfg["servant_models"] = servants
        logger.info(
            "servant models loaded from SERVANT_MODELS: %s",
            ", ".join(env_servants),
        )

    integration = GLMIntegration(
        endpoint=cfg.get("glm_api_url"),
        api_key=cfg.get("glm_api_key"),
    )
    if cfg.get("model_path"):
        os.environ.setdefault("MODEL_PATH", str(cfg["model_path"]))
    _init_memory(cfg)
    _init_servants(cfg)
    try:
        _verify_servant_health(cfg.get("servant_models", {}))
        _check_glm(integration)
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise SystemExit(1)
    except SystemExit:
        raise
    return integration


__all__ = ["initialize_crown"]
